import numpy as np
import logging
from typing import List, Tuple, Dict, Any, Optional
from scipy.optimize import linear_sum_assignment
import time

logger = logging.getLogger(__name__)

class KalmanFilter:
    """
    Simplified Kalman filter for tracking.
    Predicts object position and velocity in the 2D image plane.
    """
    def __init__(self):
        # State: [x, y, vx, vy, width, height]
        self.state = np.zeros(6)
        # Covariance matrix
        self.P = np.diag([100, 100, 25, 25, 100, 100])
        # State transition matrix
        self.F = np.array([
            [1, 0, 1, 0, 0, 0],  # x = x + vx
            [0, 1, 0, 1, 0, 0],  # y = y + vy
            [0, 0, 1, 0, 0, 0],  # vx = vx
            [0, 0, 0, 1, 0, 0],  # vy = vy
            [0, 0, 0, 0, 1, 0],  # width = width
            [0, 0, 0, 0, 0, 1]   # height = height
        ])
        # Process noise
        self.Q = np.diag([10, 10, 10, 10, 10, 10]) * 0.01
        # Measurement matrix (we observe x, y, width, height)
        self.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ])
        # Measurement noise
        self.R = np.diag([10, 10, 10, 10]) * 0.1
        self.last_update = time.time()
    
    def initialize(self, bbox: np.ndarray) -> None:
        """
        Initialize Kalman filter state from bounding box.
        
        Args:
            bbox: Bounding box in [x1, y1, x2, y2] format
        """
        self.state = np.zeros(6)
        x = (bbox[0] + bbox[2]) / 2  # center x
        y = (bbox[1] + bbox[3]) / 2  # center y
        w = bbox[2] - bbox[0]  # width
        h = bbox[3] - bbox[1]  # height
        
        self.state = np.array([x, y, 0, 0, w, h])
        self.last_update = time.time()

    def predict(self) -> np.ndarray:
        """
        Predict next state.
        
        Returns:
            Bounding box in [x1, y1, x2, y2] format
        """
        # Time difference since last update for adaptive prediction
        dt = time.time() - self.last_update
        dt = max(0.03, min(1.0, dt))  # Limit dt to reasonable range
        
        # Update state transition matrix with time factor
        self.F[0, 2] = dt
        self.F[1, 3] = dt
        
        # Predict next state
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        # Convert state to bounding box
        x, y, _, _, w, h = self.state
        return np.array([x - w/2, y - h/2, x + w/2, y + h/2])

    def update(self, bbox: np.ndarray) -> np.ndarray:
        """
        Update state with new measurement.
        
        Args:
            bbox: Bounding box in [x1, y1, x2, y2] format
        
        Returns:
            Updated bounding box in [x1, y1, x2, y2] format
        """
        # Convert bbox to center format for measurement
        x = (bbox[0] + bbox[2]) / 2
        y = (bbox[1] + bbox[3]) / 2
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        
        # Measurement vector
        z = np.array([x, y, w, h])
        
        # Update step
        y = z - (self.H @ self.state)
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.state = self.state + (K @ y)
        I = np.eye(self.state.size)
        self.P = (I - K @ self.H) @ self.P
        self.last_update = time.time()
        
        # Convert state back to bounding box
        x, y, _, _, w, h = self.state
        return np.array([x - w/2, y - h/2, x + w/2, y + h/2])

class Track:
    """Represents a tracked object with state and history."""
    
    def __init__(self, track_id: int, bbox: np.ndarray):
        """
        Initialize a track.
        
        Args:
            track_id: Unique identifier for this track
            bbox: Initial bounding box in [x1, y1, x2, y2] format
        """
        self.id = track_id
        self.kalman_filter = KalmanFilter()
        self.kalman_filter.initialize(bbox)
        self.bbox = bbox.copy()
        self.hits = 1
        self.age = 0
        self.time_since_update = 0
        self.history = [bbox.copy()]
        self.last_update_time = time.time()
        self.total_tracking_time = 0
        
    def predict(self) -> np.ndarray:
        """
        Predict the next position of this track.
        
        Returns:
            Predicted bounding box
        """
        self.bbox = self.kalman_filter.predict()
        self.age += 1
        self.time_since_update += 1
        return self.bbox
        
    def update(self, bbox: np.ndarray) -> None:
        """
        Update this track with new detection.
        
        Args:
            bbox: New detection bounding box
        """
        current_time = time.time()
        self.total_tracking_time += (current_time - self.last_update_time)
        self.last_update_time = current_time
        
        self.bbox = self.kalman_filter.update(bbox)
        self.history.append(self.bbox.copy())
        self.hits += 1
        self.time_since_update = 0
        
        # Limit history to prevent memory issues
        if len(self.history) > 30:
            self.history.pop(0)

class VehicleTracker:
    """
    Tracks vehicles across frames using Kalman filtering and Hungarian algorithm.
    Enhanced version of SimpleTracker with better association.
    """
    
    def __init__(self, max_age: int = 20, min_hits: int = 3, iou_threshold: float = 0.3):
        """
        Initialize the tracker.
        
        Args:
            max_age: Maximum frames to keep track alive without matching
            min_hits: Minimum hits needed before track is confirmed
            iou_threshold: IOU threshold for matching
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks: List[Track] = []
        self.next_id = 1
        logger.info(f"Vehicle Tracker initialized with max_age={max_age}, min_hits={min_hits}, iou_threshold={iou_threshold}")
        
    def _calculate_iou(self, box1: np.ndarray, box2: np.ndarray) -> float:
        """
        Calculate Intersection over Union between two boxes.
        
        Args:
            box1, box2: Boxes in [x1, y1, x2, y2] format
            
        Returns:
            IoU score
        """
        # Calculate intersection coordinates
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        # Calculate area of intersection and union
        width = max(0, x2 - x1)
        height = max(0, y2 - y1)
        intersection = width * height
        
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        # Return IoU
        return intersection / union if union > 0 else 0
    
    def update(self, detections: np.ndarray) -> np.ndarray:
        """
        Update tracks using new detections.
        
        Args:
            detections: Array of detection boxes in [x1, y1, x2, y2] format
            
        Returns:
            Array of tracked boxes with IDs in [x1, y1, x2, y2, track_id] format
        """
        # Initialize output array
        outputs = np.zeros((0, 5))
        
        # If no detections, just update and predict existing tracks
        if len(detections) == 0:
            # Predict new positions of existing tracks
            for track in self.tracks:
                track.predict()
                
            # Return active tracks
            for track in self.tracks:
                if track.time_since_update <= self.max_age and track.hits >= self.min_hits:
                    bbox = track.bbox
                    outputs = np.vstack((outputs, np.append(bbox, track.id)))
                    
            # Remove old tracks
            self.tracks = [track for track in self.tracks if track.time_since_update <= self.max_age]
            return outputs
        
        # Predict new locations of existing tracks
        predicted_bboxes = np.zeros((len(self.tracks), 4))
        for i, track in enumerate(self.tracks):
            predicted_bboxes[i] = track.predict()
        
        # Build cost matrix for matching
        cost_matrix = np.zeros((len(self.tracks), len(detections)))
        for i, track_bbox in enumerate(predicted_bboxes):
            for j, det_bbox in enumerate(detections):
                cost_matrix[i, j] = 1 - self._calculate_iou(track_bbox, det_bbox)
        
        # Apply Hungarian algorithm for optimal assignment
        if cost_matrix.size > 0:
            matched_indices = []
            if cost_matrix.shape[0] > 0 and cost_matrix.shape[1] > 0:
                row_indices, col_indices = linear_sum_assignment(cost_matrix)
                for row, col in zip(row_indices, col_indices):
                    if cost_matrix[row, col] <= 1 - self.iou_threshold:
                        matched_indices.append([row, col])
        else:
            matched_indices = []
        
        # Convert to numpy
        matched_indices = np.array(matched_indices)
        
        # Find unmatched detections and tracks
        unmatched_detections = []
        for d in range(len(detections)):
            if matched_indices.size > 0:
                if d not in matched_indices[:, 1]:
                    unmatched_detections.append(d)
            else:
                unmatched_detections.append(d)
                
        unmatched_tracks = []
        for t in range(len(self.tracks)):
            if matched_indices.size > 0:
                if t not in matched_indices[:, 0]:
                    unmatched_tracks.append(t)
            else:
                unmatched_tracks.append(t)
        
        # Update matched tracks
        if matched_indices.size > 0:
            for t, d in matched_indices:
                self.tracks[t].update(detections[d])
        
        # Initialize new tracks for unmatched detections
        for i in unmatched_detections:
            new_track = Track(self.next_id, detections[i])
            self.next_id += 1
            self.tracks.append(new_track)
            
        # Update unmatched tracks (they weren't detected in this frame)
        for i in unmatched_tracks:
            # Don't update, just maintain prediction
            pass
        
        # Remove old tracks
        self.tracks = [track for track in self.tracks if track.time_since_update <= self.max_age]
        
        # Build and return outputs
        for track in self.tracks:
            if track.time_since_update <= 1 and track.hits >= self.min_hits:
                bbox = track.bbox
                outputs = np.vstack((outputs, np.append(bbox, track.id)))
        
        return outputs

    def reset(self) -> None:
        """Reset the tracker state."""
        self.tracks = []
        logger.info("Vehicle tracker reset")