import time
import mysql.connector
from mysql.connector import Error
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import threading
import queue

logger = logging.getLogger(__name__)

class VehicleDatabase:
    def __init__(self, config: Dict[str, str]):
        """
        Initialize the database manager with connection parameters.
        
        Args:
            config: Database configuration with host, user, password, database
        """
        self.config = config  
        self.initialized = False

         # Test connection with detailed feedback
        connection_status = self.check_connection()
        if not connection_status:
            logger.warning("Database connection check failed, but continuing initialization...")

        # Try to establish initial connection
        try:
            self.conn = mysql.connector.connect(**self.config)
        except Error as e:
            logger.error(f"Failed to connect to database: {e}")
            self.conn = None
            
        self._initialize_database()
        
        # Create a queue and worker thread for database operations
        self.queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        
    def _initialize_database(self) -> None:
        """Initialize the database and required tables."""
        try:
            # Create database if it doesn't exist
            conn = mysql.connector.connect(
                host=self.config["host"],
                user=self.config["user"],
                password=self.config["password"]
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']}")
            cursor.close()
            conn.close()
            
            # Create necessary tables
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor()
            


            # Main vehicle records table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                track_id INT NOT NULL,
                speed INT NOT NULL,
                date_time DATETIME NOT NULL,
                vehicle_model VARCHAR(255),
                vehicle_color VARCHAR(100),
                vehicle_company VARCHAR(255),
                number_plate VARCHAR(50),
                confidence FLOAT,
                crop_image_path VARCHAR(255),
                video_source VARCHAR(255),
                processing_time FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Statistics table for aggregated data
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS speed_statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                hour INT NOT NULL,
                avg_speed FLOAT NOT NULL,
                max_speed INT NOT NULL,
                vehicle_count INT NOT NULL,
                video_source VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY date_hour_source (date, hour, video_source)
            )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Database and tables initialized successfully")
            self.initialized = True
            
        except Error as e:
            logger.error(f"Database initialization error: {e}")
            self.initialized = False
    
    def _get_connection(self) -> Optional[mysql.connector.connection.MySQLConnection]:
        """Get a database connection with retry mechanism."""
        retries = 3
        delay = 1  # seconds
        
        for attempt in range(retries):
            try:
                conn = mysql.connector.connect(**self.config)
                if conn.is_connected():
                    return conn
            except Error as e:
                logger.error(f"Database connection error (attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    logger.info(f"Retrying connection in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
        
        # If we reach here, all retries failed
        logger.critical(f"Failed to connect to database after {retries} attempts")
        logger.debug(f"Connection parameters: host={self.config.get('host')}, user={self.config.get('user')}, database={self.config.get('database')}")
        return None
    
    def check_connection(self) -> bool:
        """Test the database connection and report detailed status."""
        conn = None
        try:
            # Test basic connection to MySQL server
            logger.info(f"Testing connection to MySQL server at {self.config.get('host')}...")
            conn = mysql.connector.connect(
                host=self.config.get('host'),
                user=self.config.get('user'),
                password=self.config.get('password')
            )
            
            if not conn.is_connected():
                logger.error("Failed to connect to MySQL server")
                return False
                
            logger.info(f"Successfully connected to MySQL server at {self.config.get('host')}")
            
            # Test database existence
            cursor = conn.cursor()
            db_name = self.config.get('database')
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            
            if db_name not in databases:
                logger.error(f"Database '{db_name}' does not exist")
                return False
                
            logger.info(f"Database '{db_name}' exists")
            
            # Test table access
            conn.database = db_name
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            if 'vehicle_records' not in tables:
                logger.error("Required table 'vehicle_records' does not exist")
                return False
                
            logger.info("All database components verified successfully")
            return True
            
        except Error as e:
            logger.error(f"Connection check failed: {e}")
            return False
        finally:
            if conn and conn.is_connected():
                conn.close()
    
    def insert_vehicle(self, vehicle_data: Dict[str, Any]) -> None:
        """
        Queue a vehicle record for insertion into the database.
        
        Args:
            vehicle_data: Dictionary containing vehicle details
        """
        # Add to the processing queue
        self.queue.put(("insert_vehicle", vehicle_data))
    
    def _process_queue(self) -> None:
        """Background worker thread to process database operations."""
        while True:
            try:
                # Get operation from queue
                operation, data = self.queue.get()
                
                # Process based on operation type
                if operation == "insert_vehicle":
                    self._insert_vehicle_impl(data)
                elif operation == "update_statistics":
                    self._update_statistics_impl(data)
                # Add more operation types as needed
                
                self.queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in database worker thread: {e}")
    
    def _insert_vehicle_impl(self, vehicle_data: Dict[str, Any]) -> None:
        """
        Implementation of inserting a vehicle record into the database.
        
        Args:
            vehicle_data: Dictionary containing vehicle details
        """
        if not self.initialized:
            logger.error("Cannot insert vehicle: Database not initialized")
            return
            
        conn = self._get_connection()
        if not conn:
            logger.error('no connection')
            return
            
        try:
            cursor = conn.cursor()
            
            # Prepare vehicle data with proper formatting
            track_id = vehicle_data.get("track_id")
            speed = vehicle_data.get("speed", 0)
            date_time = vehicle_data.get("timestamp") or datetime.now()
            model = (vehicle_data.get("vehicle_model") or "unknown").lower()
            color = (vehicle_data.get("vehicle_color") or "unknown").lower()
            company = (vehicle_data.get("vehicle_company") or "unknown").lower()
            number_plate = (vehicle_data.get("number_plate") or "").replace(" ", "").upper()
            confidence = vehicle_data.get("confidence", 0.0)
            crop_image_path = vehicle_data.get("crop_image_path", "")
            video_source = vehicle_data.get("video_source", "")
            processing_time = vehicle_data.get("processing_time", 0.0)
            timestamp = vehicle_data.get("timestamp")

            if isinstance(timestamp, str):
                try:
                    # Convert string timestamp to datetime
                    from datetime import datetime
                    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except ValueError as e:
                    logger.error(f"Error parsing timestamp ({timestamp}): {e}")
                    timestamp = datetime.now()  # Fallback to current time
                # Insert query with all fields
            query = """
            INSERT INTO vehicle_records 
            (track_id, speed, date_time, vehicle_model, vehicle_color, 
            vehicle_company, number_plate, confidence, crop_image_path,
            video_source, processing_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (track_id, speed, date_time, model, color, company, 
                     number_plate, confidence, crop_image_path, video_source, 
                     processing_time)
            
            cursor.execute(query, values)
            conn.commit()
            
            logger.debug(f"Inserted vehicle record: track_id={track_id}, speed={speed}")
            
            # Queue an update to statistics
            stats_data = {
                "date": date_time.date(),
                "hour": date_time.hour,
                "speed": speed,
                "video_source": video_source
            }
            self.queue.put(("update_statistics", stats_data))
            
        except Error as e:
            logger.error(f"Error inserting vehicle record: {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    def _update_statistics_impl(self, stats_data: Dict[str, Any]) -> None:
        """
        Update speed statistics after a new vehicle record is inserted.
        
        Args:
            stats_data: Statistics data to update
        """
        if not self.initialized:
            return
            
        conn = self._get_connection()
        if not conn:
            return
            
        try:
            cursor = conn.cursor()
            
            # Get the date components
            date = stats_data["date"]
            hour = stats_data["hour"]
            speed = stats_data["speed"]
            video_source = stats_data.get("video_source", "")
            
            # First check if entry exists
            check_query = """
            SELECT id, avg_speed, max_speed, vehicle_count 
            FROM speed_statistics 
            WHERE date = %s AND hour = %s AND video_source = %s
            """
            
            cursor.execute(check_query, (date, hour, video_source))
            result = cursor.fetchone()
            
            if result:
                # Update existing record
                stat_id, avg_speed, max_speed, count = result
                
                # Calculate new average and max
                new_count = count + 1
                new_avg = ((avg_speed * count) + speed) / new_count
                new_max = max(max_speed, speed)
                
                update_query = """
                UPDATE speed_statistics 
                SET avg_speed = %s, max_speed = %s, vehicle_count = %s 
                WHERE id = %s
                """
                cursor.execute(update_query, (new_avg, new_max, new_count, stat_id))
            else:
                # Insert new record
                insert_query = """
                INSERT INTO speed_statistics 
                (date, hour, avg_speed, max_speed, vehicle_count, video_source) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (date, hour, speed, speed, 1, video_source))
                
            conn.commit()
            
        except Error as e:
            logger.error(f"Error updating statistics: {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_vehicle_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent vehicle records from the database.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of dictionaries containing vehicle records
        """
        if not self.initialized:
            return []
            
        conn = self._get_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT * FROM vehicle_records 
            ORDER BY date_time DESC 
            LIMIT %s
            """
            cursor.execute(query, (limit,))
            records = cursor.fetchall()
            return records
        except Error as e:
            logger.error(f"Error fetching vehicle records: {e}")
            return []
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def get_vehicles(self, limit=100) -> List[Dict[str, Any]]:
        """
        Get a list of vehicles from the database, limited to the specified number.
        
        Args:
            limit: Maximum number of vehicles to return
            
        Returns:
            List of vehicle dictionaries
        """
        if not self.initialized:
            logger.error("Cannot get vehicles: Database not initialized")
            return []
            
        conn = self._get_connection()
        if not conn:
            logger.error("Error getting vehicles: MySQL Connection not available.")
            return []
            
        try:
            cursor = conn.cursor(dictionary=True)
            # Query using the correct table name and columns from your schema
            query = """
                SELECT 
                    id, track_id, speed, date_time as timestamp,
                    vehicle_model, vehicle_color, vehicle_company, 
                    number_plate, confidence, crop_image_path
                FROM vehicle_records
                ORDER BY date_time DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            vehicles = cursor.fetchall()
            
            # Format data if needed
            for vehicle in vehicles:
                # Ensure consistent timestamp formatting
                if 'timestamp' in vehicle and vehicle['timestamp']:
                    if isinstance(vehicle['timestamp'], datetime):
                        vehicle['timestamp'] = vehicle['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            
            return vehicles
            
        except Error as e:
            logger.error(f"Error getting vehicles: {e}")
            return []
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        Get overall statistics as a summary object.
        
        Returns:
            Dictionary with total, avg_speed, and max_speed
        """
        if not self.initialized:
            logger.warning("Cannot get statistics: Database not initialized")
            return self._get_fallback_statistics()
            
        conn = self._get_connection()
        if not conn:
            logger.error("Error getting statistics: MySQL Connection not available.")
            return self._get_fallback_statistics()
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get total vehicles
            cursor.execute("SELECT COUNT(*) as total FROM vehicle_records")
            total_result = cursor.fetchone()
            total = total_result['total'] if total_result else 0
            
            # Get average speed
            cursor.execute("SELECT AVG(speed) as avg_speed FROM vehicle_records")
            avg_result = cursor.fetchone()
            avg_speed = round(avg_result['avg_speed'], 1) if avg_result and avg_result['avg_speed'] else 0
            
            # Get max speed
            cursor.execute("SELECT MAX(speed) as max_speed FROM vehicle_records")
            max_result = cursor.fetchone()
            max_speed = max_result['max_speed'] if max_result else 0
            
            return {
                'total': total,
                'avg_speed': avg_speed,
                'max_speed': max_speed
            }
            
        except Error as e:
            logger.error(f"Error getting statistics summary: {e}")
            return self._get_fallback_statistics()
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_statistics(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get speed statistics for the last N days.
        
        Args:
            days: Number of days to include
            
        Returns:
            List of dictionaries containing statistics
        """
        if not self.initialized:
            logger.warning("Cannot get statistics: Database not initialized")
            return []
            
        conn = self._get_connection()
        if not conn:
            logger.error("Error getting statistics: MySQL Connection not available.")
            return []
            
        try:
            cursor = conn.cursor(dictionary=True)

            # Get total vehicles
            cursor.execute("SELECT COUNT(*) as total FROM vehicle_records")
            total_result = cursor.fetchone()
            total = total_result['total'] if total_result else 0
            
            # Get average speed
            cursor.execute("SELECT AVG(speed) as avg_speed FROM vehicle_records")
            avg_result = cursor.fetchone()
            avg_speed = round(avg_result['avg_speed'], 1) if avg_result and avg_result['avg_speed'] else 0
            
            # Get max speed
            cursor.execute("SELECT MAX(speed) as max_speed FROM vehicle_records")
            max_result = cursor.fetchone()
            max_speed = max_result['max_speed'] if max_result else 0
            
            return {
                'total': total,
                'avg_speed': avg_speed,
                'max_speed': max_speed
                }
        except Error as e:
            logger.error(f"Error fetching statistics: {e}")
            return []
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
    
    def close(self) -> None:
        """Close the database connection and stop the worker thread."""
        # Wait for remaining queue items to be processed
        self.queue.join()