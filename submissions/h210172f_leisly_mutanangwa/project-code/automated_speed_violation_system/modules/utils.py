import os
import cv2
import numpy as np
import pickle
import logging
from typing import Tuple, List, Dict, Any, Optional, Union
import math
from ultralytics import YOLO
import time
import threading

logger = logging.getLogger(__name__)

def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Args:
        point1: First point (x1, y1)
        point2: Second point (x2, y2)
        
    Returns:
        Distance between the points
    """
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def calculate_center(bbox: np.ndarray) -> Tuple[float, float]:
    """
    Calculate the center point of a bounding box.
    
    Args:
        bbox: Bounding box in [x1, y1, x2, y2] format
        
    Returns:
        Center point (x, y)
    """
    return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

def load_model(model_path: str, device: str = '') -> Optional[Any]:
    """
    Load a model from file.
    
    Args:
        model_path: Path to the model file
        device: Device to load model on ('cpu', '0', etc.)
        
    Returns:
        Loaded model or None if failed
    """
    try:
        if model_path.endswith('.pt') or model_path.endswith('.pth'):
            # YOLO model
            model = YOLO(model_path)
            if device:
                model.to(device)
            logger.info(f"Loaded YOLO model from {model_path}")
            return model
        elif model_path.endswith('.pkl'):
            # Pickle model
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Loaded pickle model from {model_path}")
            return model
        else:
            logger.error(f"Unsupported model format: {model_path}")
            return None
    except Exception as e:
        logger.error(f"Error loading model {model_path}: {str(e)}")
        return None

def preprocess_frame(frame: np.ndarray, target_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
    """
    Preprocess a frame for model input.
    
    Args:
        frame: Input frame
        target_size: Optional target size (width, height)
        
    Returns:
        Preprocessed frame
    """
    if frame is None or frame.size == 0:
        raise ValueError("Empty frame received")
        
    # Resize if target size is specified
    if target_size is not None:
        frame = cv2.resize(frame, target_size)
        
    return frame

def save_results_to_csv(data: List[Dict[str, Any]], filename: str) -> bool:
    """
    Save results to a CSV file.
    
    Args:
        data: List of dictionaries containing results
        filename: Output filename
        
    Returns:
        True if successful, False otherwise
    """
    import csv
    
    try:
        if not data:
            logger.warning("No data to save")
            return False
            
        # Get field names from first record
        fieldnames = list(data[0].keys())
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
                
        logger.info(f"Results saved to {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving results to CSV: {str(e)}")
        return False

def ensure_dir_exists(path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        logger.debug(f"Created directory: {path}")

class RateLimiter:
    """Rate limiter to control execution frequency."""
    
    def __init__(self, max_calls: int, time_period: float):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed in the time period
            time_period: Time period in seconds
        """
        self.max_calls = max_calls
        self.time_period = time_period
        self.call_times = []
        self.lock = threading.Lock()
        
    def __call__(self) -> bool:
        """
        Check if a new call is allowed under the rate limit.
        
        Returns:
            True if call is allowed, False otherwise
        """
        with self.lock:
            now = time.time()
            # Remove old calls
            self.call_times = [t for t in self.call_times if now - t < self.time_period]
            
            if len(self.call_times) >= self.max_calls:
                return False
                
            self.call_times.append(now)
            return True
            

from collections import deque

class FrameRateCalculator:
    """
    Class to calculate and track frames per second (FPS).
    """
    
    def __init__(self, buffer_size: int = 30):
        """
        Initialize frame rate calculator.
        
        Args:
            buffer_size: Number of frames to use for FPS calculation
        """
        self.buffer_size = max(2, buffer_size)
        self.timestamps = deque(maxlen=buffer_size)
        self.last_update = time.time()
        
    def update(self) -> float:
        """
        Update FPS calculation with current time.
        
        Returns:
            Current FPS value
        """
        current_time = time.time()
        self.timestamps.append(current_time)
        
        # Calculate FPS
        if len(self.timestamps) >= 2:
            # Calculate time difference between oldest and newest timestamp
            time_diff = self.timestamps[-1] - self.timestamps[0]
            if time_diff > 0:
                fps = (len(self.timestamps) - 1) / time_diff
                return fps
                
        return 0.0
        
    def get_fps(self) -> float:
        """
        Get the current FPS value without updating.
        
        Returns:
            Current FPS value
        """
        if len(self.timestamps) >= 2:
            time_diff = self.timestamps[-1] - self.timestamps[0]
            if time_diff > 0:
                return (len(self.timestamps) - 1) / time_diff
        return 0.0
            
    def reset(self) -> None:
        """Reset the calculator."""
        self.timestamps = []