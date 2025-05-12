import base64
import os
import time
import cv2
import logging
from typing import Dict, Any, Tuple, List, Optional
import threading
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

class VehicleAnalyzer:
    """AI-powered vehicle analysis using Google Gemini."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the vehicle analyzer with API configuration.
        
        Args:
            config: Dictionary with configuration parameters
        """
        self.config = config
        
        # Handle different API key formats
        api_key = config.get('api_key', '')
        if isinstance(api_key, dict):
            # Extract key from dictionary if needed
            api_key = api_key.get('key', '')
        
        self.api_key = api_key
        self.model_name = config.get('model_name', 'gemini-2.0-flash')
        self.max_requests_per_minute = config.get('max_requests_per_minute', 10)
        self.model = None
        self.last_request_time = 0
        
        # Set API key as environment variable if it's a string
        if isinstance(self.api_key, str) and self.api_key:
            os.environ["GOOGLE_API_KEY"] = self.api_key

        self._initialize_model()
        
        # Create a lock for thread safety
        self.lock = threading.Lock()
        
        # Cache to avoid redundant API calls
        self.cache = {}
        
        # Rate limiting
        self.request_times = []
        
    def _initialize_model(self) -> None:
        """Initialize the Gemini model."""
        try:
            self.model = ChatGoogleGenerativeAI(model=self.model_name)
            logger.info(f"Initialized Gemini model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.model = None
    
    def _rate_limit(self) -> bool:
        """
        Implement rate limiting for API calls.
        
        Returns:
            True if request can proceed, False if rate limited
        """
        with self.lock:
            current_time = time.time()
            # Remove requests older than 60 seconds
            self.request_times = [t for t in self.request_times if current_time - t < 60]
            
            if len(self.request_times) >= self.max_requests_per_minute:
                logger.warning("Rate limit reached for Gemini API")
                return False
                
            self.request_times.append(current_time)
            return True
    
    def analyze_vehicle_image(self, image_path: str, retry_count: int = 3) -> Dict[str, str]:
        """
        Analyze a vehicle image to extract details.
        
        Args:
            image_path: Path to the image file
            retry_count: Number of retries if API call fails
            
        Returns:
            Dictionary with vehicle model, color, company, and number plate
        """
        # Check cache first
        if image_path in self.cache:
            logger.debug(f"Using cached analysis for {image_path}")
            return self.cache[image_path]
        
        # Default values
        vehicle_info = {
            "vehicle_model": "unknown",
            "vehicle_color": "unknown", 
            "vehicle_company": "unknown",
            "number_plate": ""
        }
        
        if not self.model or not os.path.exists(image_path):
            return vehicle_info
        
        # Check rate limiting
        if not self._rate_limit():
            logger.warning(f"Skipping analysis for {image_path} due to rate limiting")
            return vehicle_info
            
        try:
            for attempt in range(retry_count):
                try:
                    with open(image_path, "rb") as img_file:
                        base64_image = base64.b64encode(img_file.read()).decode("utf-8")
                    
                    # Create prompt for the model
                    message = HumanMessage(
                        content=[
                            {"type": "text", "text": "Extract ONLY these details from this vehicle image:\n| Vehicle Model | Color | Company | Number Plate |\n|--------------|--------|---------|--------------| "},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    )
                    
                    # Make API call with timeout
                    response = self.model.invoke([message])
                    response_text = response.content.strip()
                    
                    # Parse the table response
                    valid_rows = [
                        row.split("|")[1:-1]  # Split by | and remove empty first/last elements
                        for row in response_text.split("\n")
                        if "|" in row and "Vehicle Model" not in row and "---" not in row
                    ]
                    
                    if valid_rows and len(valid_rows[0]) >= 4:
                        # Use the first valid row
                        info = valid_rows[0]
                        vehicle_info = {
                            "vehicle_model": info[0].strip().lower() or "unknown",
                            "vehicle_color": info[1].strip().lower() or "unknown",
                            "vehicle_company": info[2].strip().lower() or "unknown",
                            "number_plate": info[3].strip().replace(" ", "").upper() or ""
                        }
                        
                        # Cache the result
                        self.cache[image_path] = vehicle_info.copy()
                        logger.info(f"Successfully analyzed vehicle: {vehicle_info}")
                        
                        # Limit cache size
                        if len(self.cache) > 100:
                            # Remove a random item to keep cache size reasonable
                            self.cache.pop(list(self.cache.keys())[0])
                        
                        return vehicle_info
                    
                    logger.warning(f"Invalid response format: {response_text}")
                    
                except Exception as e:
                    logger.error(f"Error in attempt {attempt+1}: {str(e)}")
                    time.sleep(2)  # Wait before retry
            
            logger.error(f"Failed to analyze image after {retry_count} attempts")
            return vehicle_info
            
        except Exception as e:
            logger.exception(f"Vehicle analysis failed: {e}")
            return vehicle_info
    
    def analyze_vehicle_batch(self, image_paths: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Analyze multiple vehicle images in a batch.
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            Dictionary mapping image paths to their analysis results
        """
        results = {}
        threads = []
        
        # Process in a thread pool with limited concurrency
        max_threads = 3  # Limit concurrency
        
        for path in image_paths:
            # Skip images that are already in cache
            if path in self.cache:
                results[path] = self.cache[path]
                continue
                
            # Wait if we've reached max thread count
            while len(threads) >= max_threads:
                # Remove completed threads
                threads = [t for t in threads if t.is_alive()]
                time.sleep(0.1)
            
            # Create and start analysis thread
            thread = threading.Thread(
                target=self._thread_analyze_image,
                args=(path, results),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        return results
    
    def _thread_analyze_image(self, image_path: str, results_dict: Dict[str, Dict[str, str]]) -> None:
        """Thread worker function to analyze an image and store the result."""
        result = self.analyze_vehicle_image(image_path)
        with self.lock:
            results_dict[image_path] = result