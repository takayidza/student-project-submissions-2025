import logging

logger = logging.getLogger(__name__)

class CoordinateManager:
    """Manages coordinate systems and transformations between original video frames and display"""
    
    def __init__(self):
        # Original video dimensions
        self.original_width = 1920  # Default, will be updated with actual video
        self.original_height = 1080
        
        # Current display dimensions
        self.display_width = 1280  # Default, will be updated with actual panel
        self.display_height = 720
        
        # Scaling factors
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        # Offset for letterboxing/pillarboxing (preserving aspect ratio)
        self.offset_x = 0
        self.offset_y = 0
        
        logger.info("CoordinateManager initialized with default dimensions")
        
    def update_original_size(self, width, height):
        """Update the dimensions of the original video frame"""
        self.original_width = width
        self.original_height = height
        self._update_scaling_factors()
        logger.debug(f"Original dimensions updated: {width}x{height}")
        
    def update_display_size(self, width, height):
        """Update the dimensions of the display area"""
        if width <= 1 or height <= 1:  # Avoid division by zero
            return
            
        self.display_width = width
        self.display_height = height
        self._update_scaling_factors()
        logger.debug(f"Display dimensions updated: {width}x{height}")
        
    def _update_scaling_factors(self):
        """Calculate scaling factors and offsets to maintain aspect ratio"""
        # Calculate scaling factors
        self.scale_x = self.display_width / self.original_width
        self.scale_y = self.display_height / self.original_height
        
        # For preserving aspect ratio
        scale = min(self.scale_x, self.scale_y)
        
        # Calculate centered offsets
        display_w = self.original_width * scale
        display_h = self.original_height * scale
        
        self.offset_x = int((self.display_width - display_w) / 2)
        self.offset_y = int((self.display_height - display_h) / 2)
        
        self.scale_x = scale
        self.scale_y = scale
        
        logger.debug(f"Scaling factors updated: scale={scale}, offset=({self.offset_x},{self.offset_y})")
    
    def frame_to_display(self, point):
        """Convert a point from original frame coordinates to display coordinates"""
        x, y = point
        display_x = int(x * self.scale_x) + self.offset_x
        display_y = int(y * self.scale_y) + self.offset_y
        return (display_x, display_y)
    
    def display_to_frame(self, point):
        """Convert a point from display coordinates to original frame coordinates"""
        x, y = point
        frame_x = int((x - self.offset_x) / self.scale_x)
        frame_y = int((y - self.offset_y) / self.scale_y)
        return (frame_x, frame_y)
    
    def scale_dimensions(self, width, height):
        """Scale dimensions from original to display"""
        return (int(width * self.scale_x), int(height * self.scale_y))
    
    def scale_font_size(self, size):
        """Scale font size based on display dimensions"""
        # Scale font based on average of width and height scaling
        scale_factor = (self.scale_x + self.scale_y) / 2
        return max(1, size * scale_factor)
    
    def scale_line_thickness(self, thickness):
        """Scale line thickness based on display dimensions"""
        scale_factor = (self.scale_x + self.scale_y) / 2
        return max(1, int(thickness * scale_factor))