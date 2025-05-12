import math
import cv2
import numpy as np
import time
import os
import logging
import threading
import pickle
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any

from ultralytics import YOLO
from ultralytics.engine.results import Results
from ultralytics.utils.plotting import Annotator

from modules.tracker import VehicleTracker
from modules.ai_analyzer import VehicleAnalyzer
from modules.database import VehicleDatabase
from modules.utils import calculate_distance, calculate_center, load_model

logger = logging.getLogger(__name__)

class SpeedEstimator:
    """
    Speed estimation for vehicles using YOLOv5 detection and custom tracking.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        database: VehicleDatabase = None,
        ai_analyzer: VehicleAnalyzer = None
    ):
        self.config = config
        self.database = database
        self.ai_analyzer = ai_analyzer

        self.model_path = config.get('model_path', 'yolo12s.pt')
        self.line_width = config.get('line_width', 2)
        self.conf_threshold = config.get('confidence_threshold', 0.25)
        self.debug_mode = config.get('debug_mode', False)
        self.vehicle_classes = config.get('vehicle_classes', ['car', 'truck', 'bus', 'motorcycle'])
        self.crop_dir = config.get('crop_dir', 'crop')
        self.conversion_model_path = config.get('conversion_model_path', 'conversion_factor_model.pkl')
        self.min_pixel_movement = config.get('min_pixel_movement', 100)  # pixels to trigger speed calc

        os.makedirs(self.crop_dir, exist_ok=True)
        self._initialize_models()

        self.entry_info = {}        # track_id -> (entry_time, entry_center)
        self.trk_pt = {}            # track_id -> last_update_time
        self.trk_pp = {}            # track_id -> last_position
        self.spd = {}               # track_id -> speed
        self.speed_history = {}     # track_id -> [list of speed measurements]
        self.recorded_ids = set()   # track_ids that have been recorded to the database

        self.stats = {
            'vehicles_detected': 0,
            'avg_speed': 0,
            'max_speed': 0
        }

        self.lock = threading.Lock()

    def _initialize_models(self) -> None:
        try:
            self.model = YOLO(self.model_path)
            logger.info(f"Loaded YOLO model from {self.model_path}")

            self.tracker = VehicleTracker(
                max_age=self.config.get('tracker_max_age', 20),
                min_hits=self.config.get('tracker_min_hits', 3),
                iou_threshold=self.config.get('tracker_iou_threshold', 0.3)
            )

            self.conversion_model = None
            try:
                if os.path.exists(self.conversion_model_path):
                    with open(self.conversion_model_path, 'rb') as f:
                        self.conversion_model = pickle.load(f)
                    logger.info(f"Loaded conversion model from {self.conversion_model_path}")
                else:
                    logger.warning(f"Conversion model file not found at {self.conversion_model_path}")
                    self.conversion_model = lambda x: x * 3.6  # Simple m/s to km/h conversion
                    logger.info("Using default conversion factor (3.6)")
            except Exception as e:
                logger.error(f"Failed to load conversion model: {str(e)}")
                self.conversion_model = lambda x: x * 3.6
                logger.info("Using default conversion factor (3.6) due to error")
        except Exception as e:
            logger.error(f"Failed to initialize models: {str(e)}")
            raise RuntimeError(f"Failed to initialize speed estimator: {str(e)}")

    def log_debug(self, message: str) -> None:
        logger.debug(message)

    def convert_to_real_speed(self, pixel_speed: float) -> float:
        try:
            if hasattr(self.conversion_model, 'predict'):
                real_speed = float(self.conversion_model.predict([[pixel_speed]])[0])
                real_speed = real_speed * 3.6 * 10
            elif callable(self.conversion_model):
                real_speed = float(self.conversion_model(pixel_speed))
                real_speed = real_speed * 10
            else:
                real_speed = (pixel_speed * 0.1) * 10

            logger.warning(f"Pixel speed: {pixel_speed:.2f} -> Real speed: {real_speed:.2f} km/h")
            if real_speed > 190:
                logger.warning(f"Unrealistic speed detected: {real_speed:.1f} km/h, capping to 180 km/h")
                real_speed = 180
            return max(0, min(300, real_speed))
        except Exception as e:
            logger.error(f"Speed conversion error: {str(e)}")
            return pixel_speed * 0.1

    def analyze_and_store_vehicle(
        self,
        image_path: str,
        track_id: int,
        speed: float,
        timestamp: str,
        video_source: str = "",
        processing_time: float = 0.0
    ) -> None:
        print('started analysing and saving..')
        speed_threshold = 40.0  # km/h
        if speed < speed_threshold:
            print(f"Speed {speed} km/h is below threshold, skipping analysis")
            logger.info(f"Speed {speed} km/h is below threshold, skipping analysis")
            return

        vehicle_info = {
            "vehicle_model": "Sedan",
            "vehicle_color": "Unknown",
            "vehicle_company": "Unknown",
            "number_plate": f"UNK-{track_id}"
        }
        try:
            if self.ai_analyzer is not None:
                vehicle_info = self.ai_analyzer.analyze_vehicle_image(image_path, 2)
            logger.info(f"Vehicle info for track_id={track_id}: {vehicle_info}")
            print(f"Vehicle info for track_id={track_id}: {vehicle_info}")
        except Exception as e:
            print(f'Error analyzing vehicle: {str(e)}')
            logger.exception(f"Error analyzing vehicle data: {str(e)}")

        try:
            if isinstance(timestamp, str):
                try:
                    timestamp_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    timestamp_obj = datetime.now()
            else:
                timestamp_obj = timestamp

            if self.database is not None:
                vehicle_data = {
                    "track_id": int(track_id),
                    "speed": int(round(speed)),
                    "timestamp": timestamp_obj,
                    "vehicle_model": vehicle_info.get("vehicle_model", "unknown"),
                    "vehicle_color": vehicle_info.get("vehicle_color", "unknown"),
                    "vehicle_company": vehicle_info.get("vehicle_company", "unknown"),
                    "number_plate": vehicle_info.get("number_plate", ""),
                    "confidence": 1.0,
                    "crop_image_path": image_path,
                    "video_source": video_source,
                    "processing_time": processing_time
                }
                print(f'insert zone..{vehicle_data}*')
                self.database.insert_vehicle(vehicle_data)
                logger.info(f"Vehicle data stored for track_id={track_id}, speed={speed:.1f} km/h")
            else:
                print('database not there..')
                logger.warning("Database not available, skipping data storage")
        except Exception as e:
            print(f'Error storing vehicle data: {str(e)}')
            logger.exception(f"Error storing vehicle data: {str(e)}")

    def estimate_speed(
        self,
        frame: np.ndarray,
        expected_fps: float,
        measured_fps: float
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Detect vehicles and estimate their speeds in a video frame.
        No explicit ROI: speed is calculated from first detection to significant movement.
        """
        start_time = time.time()
        stats_update = {
            'vehicles_detected': 0,
            'avg_speed': 0,
            'max_speed': 0
        }

        if frame is None or frame.size == 0:
            logger.warning("Empty frame received for processing")
            return frame, stats_update

        try:
            results = self.model.predict(
                source=frame,
                conf=self.conf_threshold,
                verbose=False
            )

            if not results or len(results) == 0:
                return frame, stats_update

            if hasattr(results[0].boxes, "xyxy"):
                det_boxes = results[0].boxes.xyxy.cpu().numpy()
                det_confs = results[0].boxes.conf.cpu().numpy()
                det_classes = results[0].boxes.cls.cpu().numpy()
            else:
                det_boxes = np.array([])
                det_confs = np.array([])
                det_classes = np.array([])
                if hasattr(results[0], 'boxes') and hasattr(results[0].boxes, 'data'):
                    boxes_data = results[0].boxes.data.cpu().numpy()
                    if boxes_data.shape[1] >= 6:
                        det_boxes = boxes_data[:, :4]
                        det_confs = boxes_data[:, 4]
                        det_classes = boxes_data[:, 5]

            valid_class_indices = []
            for i, cls_id in enumerate(det_classes):
                class_name = self.model.names[int(cls_id)].lower() if hasattr(self.model, "names") else ""
                if class_name in self.vehicle_classes:
                    valid_class_indices.append(i)

            filtered_boxes = det_boxes[valid_class_indices] if valid_class_indices else np.array([])

            if len(filtered_boxes) == 0:
                return frame, stats_update

            tracker_output = self.tracker.update(filtered_boxes)

            if tracker_output.size == 0:
                return frame, stats_update

            boxes = tracker_output[:, :4]
            track_ids = tracker_output[:, 4].astype(int)

            annotated = frame.copy()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            speeds = []

            print(f"Detected {len(filtered_boxes)} vehicles, {len(track_ids)} tracked objects")

            for box, track_id in zip(boxes, track_ids):
                stats_update['vehicles_detected'] += 1
                curr_center = calculate_center(box)

                # Start tracking as soon as a new vehicle is detected
                if track_id not in self.entry_info:
                    self.entry_info[track_id] = (time.time(), curr_center)
                    self.speed_history[track_id] = []
                    self.log_debug(f"Track {track_id} detected at {curr_center}")

                entry_time, entry_center = self.entry_info[track_id]
                distance = calculate_distance(entry_center, curr_center)

                if distance >= self.min_pixel_movement and track_id not in self.recorded_ids:
                    duration = time.time() - entry_time
                    if duration > 0:
                        pixel_speed = distance / duration
                        # Adjust for FPS differences
                        fps_adjusted_speed = pixel_speed * (expected_fps / measured_fps if measured_fps > 0 else 1.0)
                        real_speed = self.convert_to_real_speed(fps_adjusted_speed)
                        self.spd[track_id] = round(real_speed, 1)
                        speeds.append(self.spd[track_id])

                        x1, y1, x2, y2 = map(int, box)
                        crop_img = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]
                        if crop_img.size != 0:
                            crop_filename = os.path.join(
                                self.crop_dir,
                                f"{track_id}_{current_time.replace(':','-')}.jpg"
                            )
                            cv2.imwrite(crop_filename, crop_img)
                            if self.ai_analyzer and self.database:
                                try:
                                    print('SAVING TO DB begin..**')
                                    threading.Thread(
                                        target=self.analyze_and_store_vehicle,
                                        args=(crop_filename, track_id, real_speed, current_time,
                                              os.path.basename(self.config.get('video_source', '')),
                                              time.time() - start_time),
                                        daemon=True
                                    ).start()
                                except Exception as e:
                                    print('Exception in saving to db...')
                        self.recorded_ids.add(track_id)
                    if track_id in self.entry_info:
                        del self.entry_info[track_id]

                # Update tracking history
                self.trk_pt[track_id] = time.time()
                self.trk_pp[track_id] = curr_center

                # Annotate the vehicle on the frame
                cls_name = "Vehicle"
                speed_text = f"{self.spd.get(track_id, 'N/A')} km/h" if track_id in self.spd else "Calculating..."
                label = f"{cls_name} {track_id} ({speed_text})"
                annotator = Annotator(annotated, line_width=self.line_width)
                annotator.box_label(box, label, color=(0, 255, 0))

                if self.debug_mode:
                    if track_id in self.trk_pp:
                        prev_center = self.trk_pp[track_id]
                        cv2.line(
                            annotated,
                            (int(prev_center[0]), int(prev_center[1])),
                            (int(curr_center[0]), int(curr_center[1])),
                            color=(0, 255, 255),
                            thickness=1
                        )
                        if track_id in self.spd:
                            speed_text = f"{self.spd[track_id]} km/h"
                            cv2.putText(
                                annotated,
                                speed_text,
                                (int(curr_center[0]) + 10, int(curr_center[1])),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (255, 255, 255),
                                2
                            )
                            cv2.putText(
                                annotated,
                                speed_text,
                                (int(curr_center[0]) + 10, int(curr_center[1])),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (0, 128, 255),
                                1
                            )

            if speeds:
                stats_update['avg_speed'] = round(sum(speeds) / len(speeds), 1)
                stats_update['max_speed'] = round(max(speeds), 1)

            cv2.putText(
                annotated,
                f"Expected FPS: {expected_fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )
            cv2.putText(
                annotated,
                f"Actual FPS: {measured_fps:.1f}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            processing_time = time.time() - start_time
            cv2.putText(
                annotated,
                f"Processing: {processing_time*1000:.1f}ms",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2
            )

            if self.debug_mode:
                roi_text = f"Active Tracks: {len(self.entry_info)}"
                cv2.putText(
                    annotated,
                    roi_text,
                    (10, annotated.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )
                entry_text = "Entries: " + ", ".join([str(tid) for tid in self.entry_info.keys()])
                cv2.putText(
                    annotated,
                    entry_text,
                    (10, annotated.shape[0] - 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1
                )

            return annotated, stats_update

        except Exception as e:
            logger.exception(f"Error in speed estimation: {str(e)}")
            return frame, stats_update

    def reset(self) -> None:
        """Reset all tracking information."""
        with self.lock:
            self.entry_info = {}
            self.trk_pt = {}
            self.trk_pp = {}
            self.spd = {}
            self.speed_history = {}
            self.recorded_ids = set()
            logger.info("Speed estimator state reset")