import os
import logging
from logging.handlers import RotatingFileHandler
import time
from typing import Dict, Any

def setup_logging(log_dir: str = 'logs', level: int = logging.INFO) -> None:
    """
    Configure application logging.
    
    Args:
        log_dir: Directory to store log files
        level: Base logging level
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(log_dir, f"vehicle_tracking_{timestamp}.log")
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)-8s | %(name)-25s | %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create and add file handler (with rotation)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    root_logger.addHandler(file_handler)
    
    # Create and add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)  # Console shows INFO and above
    root_logger.addHandler(console_handler)
    
    # Set specific log levels for different modules
    module_levels = {
        'modules.speed_estimator': logging.INFO,
        'modules.tracker': logging.INFO,
        'modules.database': logging.INFO,
        'modules.ai_analyzer': logging.INFO
    }
    
    for module, level in module_levels.items():
        logging.getLogger(module).setLevel(level)
    
    logging.info(f"Logging initialized. Log file: {log_file}")

class LogCapture:
    """Class to capture logs for display in GUI."""
    
    def __init__(self, max_entries: int = 100):
        """
        Initialize log capture.
        
        Args:
            max_entries: Maximum number of log entries to store
        """
        self.logs = []
        self.max_entries = max_entries
        self.handler = None
        self.setup()
        
    def setup(self) -> None:
        """Set up log handler."""
        class GUILogHandler(logging.Handler):
            def __init__(self, callback):
                super().__init__()
                self.callback = callback
                
            def emit(self, record):
                log_entry = self.format(record)
                self.callback(record, log_entry)
                
        # Create handler
        self.handler = GUILogHandler(self.add_log)
        self.handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s'))
        self.handler.setLevel(logging.INFO)
        
        # Add to root logger
        logging.getLogger().addHandler(self.handler)
        
    def add_log(self, record: logging.LogRecord, formatted_log: str) -> None:
        """
        Add a log entry to the capture.
        
        Args:
            record: Log record
            formatted_log: Formatted log message
        """
        self.logs.append({
            'time': record.created,
            'level': record.levelname,
            'message': record.getMessage(),
            'formatted': formatted_log
        })
        
        # Keep only max_entries
        if len(self.logs) > self.max_entries:
            self.logs.pop(0)
            
    def get_logs(self, level: str = None) -> list:
        """
        Get captured logs, optionally filtered by level.
        
        Args:
            level: Optional log level to filter by
            
        Returns:
            List of log entries
        """
        if level:
            return [log for log in self.logs if log['level'] == level]
        return self.logs
        
    def clear(self) -> None:
        """Clear captured logs."""
        self.logs = []