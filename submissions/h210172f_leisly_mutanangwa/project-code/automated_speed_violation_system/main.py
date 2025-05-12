import os
import sys
import logging
import threading
import time
import tkinter as tk
import argparse
from datetime import datetime
from typing import Dict, Tuple, Optional, Any, List
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Enable DPI awareness


# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"vehicle_tracking_{datetime.now().strftime('%Y%m%d-%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Logging initialized. Log file: {log_file}")

# Import configuration
from config.settings import (
    DATABASE_SETTINGS,
    TRACKER_SETTINGS,
    MODEL_SETTINGS,
    SPEED_ESTIMATOR_SETTINGS,
    AI_SETTINGS,
    APP_SETTINGS,
)

# Import modules
from modules.database import VehicleDatabase
from modules.ai_analyzer import VehicleAnalyzer
from modules.speed_estimator import SpeedEstimator
from modules.gui import SpeedEstimatorGUI
from modules.utils import FrameRateCalculator

# Import Flask for web dashboard
from flask import Flask, render_template, jsonify, request, send_from_directory

class Application:
    """
    Main application class that coordinates all components.
    """
    
    def __init__(self, use_gui=True):
        """Initialize the application components."""
        logger.info("Initializing vehicle speed estimation system")
        self.use_gui = use_gui
        
        # Initialize database
        try:
            self.database = VehicleDatabase(DATABASE_SETTINGS)
            logger.info("Database initialized")
        except Exception as e:
            logger.exception(f"Error initializing database: {e}")
            self.database = None
            
        # Initialize AI analyzer
        try:
            # Make sure we have a proper API key string
            if isinstance(AI_SETTINGS.get('api_key'), dict):
                api_key = AI_SETTINGS.get('api_key', {}).get('key', '')
                AI_SETTINGS['api_key'] = api_key
                
            self.ai_analyzer = VehicleAnalyzer(AI_SETTINGS)
            logger.info("AI analyzer initialized")
        except Exception as e:
            logger.exception(f"Error initializing AI analyzer: {e}")
            self.ai_analyzer = None
            
        # Initialize speed estimator
        try:
            self.speed_estimator = SpeedEstimator(SPEED_ESTIMATOR_SETTINGS , 
                self.database, 
                self.ai_analyzer,
            )
            logger.info("Speed estimator initialized")
        except Exception as e:
            logger.exception(f"Error initializing speed estimator: {e}")
            self.speed_estimator = None
            
        # Initialize FPS calculator
        self.fps_calculator = FrameRateCalculator(buffer_size=30)
        
        # Initialize GUI if needed
        if use_gui:
            try:
                # Create a root window for the GUI
                self.root = tk.Tk()
                self.root.title(APP_SETTINGS.get('title', 'Vehicle Speed Estimator'))
                self.root.geometry(f"{APP_SETTINGS.get('width', 1100)}x{APP_SETTINGS.get('height', 700)}")
                
                # Initialize GUI with correct parameters based on what it expects
                self.gui = SpeedEstimatorGUI(
                    root=self.root,
                    process_frame_callback=self.process_frame
                )
                
                # Set up ROI callback if method exists
                if hasattr(self.gui, 'on_roi_defined'):
                    self.gui.on_roi_defined = self._on_roi_defined
                
                logger.info("GUI initialized successfully")
            except Exception as e:
                logger.exception(f"Error initializing GUI: {e}")
                self.gui = None
            
        # Initialize Flask app for web dashboard
        self.flask_app = self._create_flask_app()
        
    def _create_flask_app(self):
        """Create and configure the Flask application for the dashboard."""
        app = Flask(__name__,
                   static_folder='static',
                   template_folder='templates')
                   
        # Speed violation thresholds
        speed_limits = {
            'urban': 50,        # km/h in urban areas
            'rural': 90,        # km/h on rural roads
            'highway': 120      # km/h on highways
        }
        
        # Default to urban speed limit
        current_speed_limit = speed_limits['urban']
        
        @app.route('/')
        def index():
            """Serve the dashboard on the index route"""
            return render_template('index.html')
        
        @app.route('/static/<path:path>')
        def serve_static(path):
            """Serve static files"""
            return send_from_directory('static', path)
        
        @app.route('/api/speed-monitoring')
        def get_speed_monitoring():
            """API endpoint to get speed monitoring data"""
            try:
                # Get statistics from database
                stats = self.database.get_statistics_summary() if self.database else {}
                
                # Get recent vehicles
                vehicles = self.database.get_vehicles(limit=100) if self.database else []
                
                # Filter for violations and sort by timestamp (newest first)
                violations = []
                for vehicle in vehicles:
                    if vehicle.get('speed', 0) > current_speed_limit:
                        try:
                           violations.append({
                                'id': vehicle.get('track_id', 0),
                                'vehicle': f"{vehicle.get('vehicle_color', 'Unknown')} {vehicle.get('vehicle_model', 'Vehicle')}",
                                'speed': vehicle.get('speed', 0),
                                'number_plate': vehicle.get('number_plate', 'Unknown'),
                                'timestamp': vehicle.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                            })
                        except Exception as e:
                            logger.error(f"Error processing vehicle data: {e}")
                
                # Sort by timestamp (newest first)
                violations.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Count violation types
                mild_violations = sum(1 for v in violations if current_speed_limit < v['speed'] <= current_speed_limit * 1.1)
                moderate_violations = sum(1 for v in violations if current_speed_limit * 1.1 < v['speed'] <= current_speed_limit * 1.25)
                severe_violations = sum(1 for v in violations if v['speed'] > current_speed_limit * 1.25)
                
                # Create response data
                print("stats: ", stats)
                response = {
                    'total_vehicles': stats.get('total') if stats!=[] else 0,
                    'average_speed': stats.get('avg_speed') if stats!=[] else 0,
                    'maximum_speed': stats.get('max_speed') if stats!=[] else 0,
                    'total_violations': len(violations) if stats!=[] else 0,
                    'mild_violations': mild_violations,
                    'moderate_violations': moderate_violations,
                    'severe_violations': severe_violations,
                    'recent_violations': violations[:10],  # Get 10 most recent violations
                    'speed_limit': current_speed_limit
                }
                
                return jsonify(response)
                
            except Exception as e:
                logger.exception(f"Error getting speed monitoring data: {e}")
                return jsonify({
                    'error': str(e),
                    'total_vehicles': 0,
                    'average_speed': 0,
                    'maximum_speed': 0,
                    'total_violations': 0,
                    'mild_violations': 0,
                    'moderate_violations': 0,
                    'severe_violations': 0,
                    'recent_violations': [],
                    'speed_limit': current_speed_limit
                })
        
        @app.route('/api/speed-limit', methods=['POST'])
        def set_speed_limit():
            """Set the current speed limit"""
            nonlocal current_speed_limit
            data = request.json
            limit_type = data.get('type', 'urban')
            
            if limit_type in speed_limits:
                current_speed_limit = speed_limits[limit_type]
                return jsonify({'success': True, 'speed_limit': current_speed_limit})
            
            return jsonify({'success': False, 'error': 'Invalid limit type'})
        
        return app
            
    def _on_roi_defined(self, region_points):
        """
        Handle ROI definition from the GUI.
        
        Args:
            region_points: List of (x, y) points defining the ROI
        """
        if self.speed_estimator:
            self.speed_estimator.set_region(region_points)
            logger.info(f"ROI updated through GUI: {region_points}")
        
    def process_frame(self, frame, frame_number=0):
        """
        Process a video frame - this is the callback used by the GUI.
        
        Args:
            frame: Video frame to process
            frame_number: Current frame number for timing
                
        Returns:
            Tuple containing processed frame and statistics dict
        """
        if frame is None or self.speed_estimator is None:
            return frame, {}
            
        try:
            # Update FPS calculator
            measured_fps = self.fps_calculator.update()
            if measured_fps == 0:
                measured_fps = 30  # Default if not enough samples
                
            # Process the frame
            expected_fps = 30  # Default if not available from video source
            if hasattr(self, 'video_fps') and self.video_fps > 0:
                expected_fps = self.video_fps
                
            # Process frame with speed estimator - remove frame_number parameter
            processed_frame, stats = self.speed_estimator.estimate_speed(
                frame, 
                expected_fps=expected_fps, 
                measured_fps=measured_fps
            )
            
            # Add FPS to statistics
            stats['fps'] = round(measured_fps, 1)
            
            return processed_frame, stats
            
        except Exception as e:
            logger.exception(f"Error processing frame: {e}")
            return frame, {}
            
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics from database.
        
        Returns:
            Dictionary with statistics
        """
        if self.database:
            return self.database.get_statistics()
        return {}
        
    def set_video_params(self, fps: float, total_frames: int) -> None:
        """
        Set video parameters from the loaded video.
        
        Args:
            fps: Frames per second of the video
            total_frames: Total frames in the video
        """
        self.video_fps = fps
        self.total_frames = total_frames
        
        # Update speed estimator with video FPS
        if self.speed_estimator:
            self.speed_estimator.set_source_fps(fps)
            
    def run_gui(self) -> None:
        """Run the application GUI main loop."""
        if not self.use_gui or not hasattr(self, 'root') or self.root is None:
            logger.error("Cannot start GUI: not initialized or disabled")
            return
            
        try:
            logger.info("Starting application GUI main loop")
            self.root.mainloop()  # Use root.mainloop() instead of self.gui.run()
        except Exception as e:
            logger.exception(f"Error in GUI main loop: {e}")
            
    def run_web(self, host='0.0.0.0', port=5000, debug=False) -> None:
        """Run the web dashboard."""
        if not hasattr(self, 'flask_app') or self.flask_app is None:
            logger.error("Cannot start web dashboard: Flask app not initialized")
            return
            
        try:
            logger.info(f"Starting web dashboard on {host}:{port}")
            self.flask_app.run(host=host, port=port, debug=debug)
        except Exception as e:
            logger.exception(f"Error in web dashboard: {e}")
            
    def run(self, mode='both', web_host='0.0.0.0', web_port=5000, web_debug=False) -> None:
        """
        Run the application with specified components.
        
        Args:
            mode: 'gui', 'web', or 'both'
            web_host: Host for web dashboard
            web_port: Port for web dashboard
            web_debug: Debug mode for web dashboard
        """
        if mode == 'gui':
            self.run_gui()
        elif mode == 'web':
            self.run_web(web_host, web_port, web_debug)
        elif mode == 'both':
            # Run web in a separate thread
            web_thread = threading.Thread(
                target=self.run_web,
                args=(web_host, web_port, web_debug),
                daemon=True
            )
            web_thread.start()
            
            # Run GUI in main thread
            self.run_gui()
        else:
            logger.error(f"Invalid run mode: {mode}")
            
    def shutdown(self) -> None:
        """Clean up and shutdown the application."""
        logger.info("Application shutting down")
        if hasattr(self, 'database') and self.database:
            self.database.close()
        logger.info("Application shut down")

def main():
    """
    Main function to run the application.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Vehicle Speed Monitoring System')
    parser.add_argument('--mode', choices=['gui', 'web', 'both'], default='both',
                      help='Run mode: gui, web, or both')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--host', default='0.0.0.0', help='Web server host')
    parser.add_argument('--port', type=int, default=5000, help='Web server port')
    
    args = parser.parse_args()
    
    # Create application with GUI enabled if needed
    use_gui = args.mode in ['gui', 'both']
    app = Application(use_gui=use_gui)
    
    try:
        # Run the application in specified mode
        app.run(mode=args.mode, web_host=args.host, web_port=args.port, web_debug=args.debug)
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
    finally:
        app.shutdown()

if __name__ == "__main__":
    main()