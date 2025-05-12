"""
Application configuration settings.
"""

import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")
CROP_DIR = os.path.join(BASE_DIR, "crop")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
for directory in [MODELS_DIR, DATA_DIR, CROP_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Model settings
MODEL_SETTINGS = {
    'model_path': os.path.join(MODELS_DIR, "yolo12s.pt"),
    'conversion_model_path': os.path.join(MODELS_DIR, "conversion_factor_model.pkl"),
    'confidence_threshold': 0.25,
    'device': '',  # Empty for auto-select, 'cpu', 'cuda:0', etc.
}

# Database settings
DATABASE_SETTINGS = {
    'host': 'localhost',
    'user': 'root',
    'password': 'TGVpc2x5',
    'database': 'vehicle_tracking',
    'port': 3306,
}

# AI analyzer settings
AI_SETTINGS = {
    'api_key': 'AIzaSyDs_CKVBKtpCBXGlVuCIM-kbxvo5n8-eRA',  # Replace with your actual API key
    'model_name': 'gemini-2.0-flash',
    'max_requests_per_minute': 10,
}

# Tracker settings
TRACKER_SETTINGS = {
    'max_age': 20,
    'min_hits': 3,
    'iou_threshold': 0.3,
}

# Speed estimator settings
SPEED_ESTIMATOR_SETTINGS = {
    'line_width': 2,
    # Try a wider ROI that covers more of the frame
    # 'region': [(100, 100), (400, 400)],
    'region': [(100, 50), (400, 250)],
    # 'region': [(160, 346), (820, 346)],  # Default ROI
    'debug_mode': False,
    'vehicle_classes': ['car', 'truck', 'bus', 'motorcycle'],
    'crop_dir': CROP_DIR,
    'conversion_model_path': os.path.join(MODELS_DIR, "conversion_factor_model.pkl")
}

# Application settings
APP_SETTINGS = {
    'title': 'Vehicle Speed Estimator',
    'width': 1280,
    'height': 720,
    'preserve_aspect_ratio': True,
    'theme': 'light',
    'default_font_size': 12,
    'scaling_factor': 1.0
}

# Combine all settings for easy access
SETTINGS = {
    'model': MODEL_SETTINGS,
    'database': DATABASE_SETTINGS,
    'ai': AI_SETTINGS,
    'tracker': TRACKER_SETTINGS,
    'speed_estimator': SPEED_ESTIMATOR_SETTINGS,
    'app': APP_SETTINGS
}