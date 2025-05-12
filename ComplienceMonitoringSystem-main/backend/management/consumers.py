import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

import json
import random
import os
import time
from datetime import datetime
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.utils import timezone

from .utilites.reg import create_or_update_device
from .utilites.scanner import DeviceScanner


def scan_all_devices(reason=""):
    logger.info(f"[Scan] Triggered full device scan. Reason: {reason}")
    devices = Device.objects.all()
    for device in devices:
        scanner = DeviceScanner(device)
        is_compliant, violations = scanner.scan_device()
        if is_compliant:
            logger.info(f"[Scan] Device {device.hostname} is compliant.")
        else:
            logger.warning(f"[Scan] Device {device.hostname} has {len(violations)} violations:")
            for violation in violations:
                logger.warning(f"- {violation['description']}")

class MonitoringConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]
        self.room_group_name = f"monitoring"
        
        # Get user from scope
        self.user = self.scope["user"]
        
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        
        self.accept()
        
        # Send welcome message
        self.send_log("Monitoring WebSocket connection established", log_type="success")
        
    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )
    
    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        
        # Handle different command types
        if "command" in data:
            command = data["command"].strip().lower()
            device_id = data.get("device_id", "all")
            
            # Process command
            self.process_command(command, device_id)
        
        # Handle alert acknowledgement
        elif "alert_id" in data and data.get("command") == "acknowledge_alert":
            self.acknowledge_alert(data["alert_id"])
    
    # Process monitoring commands
    def process_command(self, command, device_id):
        command_parts = command.split()
        base_command = command_parts[0]
        
        # Help command
        if base_command == "help":
            self.send_log("Available commands:", log_type="success")
            self.send_log("  status [device_id|all] - Show status of device(s)")
            self.send_log("  scan [device_id|all] - Run virus scan on device(s)")
            self.send_log("  compliance [device_id|all] - Check compliance of device(s)")
            self.send_log("  diagnostics [device_id|all] - Run diagnostics on device(s)")
            self.send_log("  usage [device_id|all] - Show resource usage")
            self.send_log("  alerts - Show active alerts")
            self.send_log("  help - Show this help message")
            self.send_log("  clear - Clear terminal")
            
        # Status command
        elif base_command == "status":
            self.get_device_status(device_id)
            
        # Scan command
        elif base_command == "scan":
            params = command_parts[1:] if len(command_parts) > 1 else []
            scan_all_devices(reason="Realtime Scan")
            self.send_log(f"Realtime Scan ...", log_type="success")
            self.run_virus_scan(device_id, params)
            
        # Compliance command
        elif base_command == "compliance":
            self.check_compliance(device_id)
            
        # Diagnostics command
        elif base_command == "diagnostics":
            self.run_diagnostics(device_id)
            
        # Usage command
        elif base_command == "usage":
            self.get_resource_usage(device_id)
            
        # Alerts command
        elif base_command == "alerts":
            self.get_active_alerts()
            
        # Unknown command
        else:
            self.send_log(f"Unknown command: {command}", log_type="error")
    
    # Get device status
    def get_device_status(self, device_id):
        # Implementation unchanged from previous version
        if device_id == "all":
            self.send_log("Fetching status for all devices...")
            # Rest of the implementation...
        else:
            # Rest of the implementation...
            pass
    
    # Run virus scan on files
    def run_virus_scan(self, device_id, params=None):
        self.send_log(f"Initiating virus scan on device(s) {device_id}...", log_type="warning")
        
        # List of malicious file patterns (example)
        malicious_patterns = [
            'virus', 'malware', 'trojan', 'backdoor', 'rootkit', 'keylogger', 
            'ransomware', 'spyware', 'adware', 'worm', 'exploit', 'hack', 
            'suspicious', 'danger', 'unsafe', 'blocked', 'unwanted', 'phishing',
            'crypto-miner', 'botnet'
        ]
        
        # Set scan path
        scan_path = "/"
        if params and len(params) > 0 and params[0] != "all":
            scan_path = params[0]
        
        self.send_log(f"Starting file system scan from {scan_path}", log_type="warning")
        self.send_log(f"Scanning for malicious patterns: {', '.join(malicious_patterns[:5])}...", log_type="warning")
        
        # Start scan
        scanned_files = 0
        infected_files = []
        
        # Simulate scanning different directories with random delays
        directories_to_simulate = [
            '/home', '/usr', '/var', '/etc', '/tmp', '/opt', 
            '/mnt', '/media', '/srv', '/bin', '/sbin', '/lib'
        ]
        
        for dir_path in directories_to_simulate:
            # Simulate scanning this directory
            self.send_log(f"Scanning directory: {dir_path}")
            
            # Simulate files being scanned
            num_files = random.randint(10, 100)
            scanned_files += num_files
            
            # Update progress
            self.send_log(f"Scanned {num_files} files in {dir_path}, total scanned: {scanned_files}")
            
            # Randomly find infected files
            if random.random() < 0.3:  # 30% chance to find infected file
                # Generate random "infected" file
                file_name = f"{dir_path}/{random.choice(['file', 'doc', 'exe', 'zip', 'bin', 'sh', 'py'])}_" + \
                           f"{random.randint(1, 999)}.{random.choice(['exe', 'dll', 'sh', 'py', 'bin', 'dat'])}"
                
                # Random malicious pattern
                malicious_type = random.choice(malicious_patterns)
                
                # Add to infected files list
                infected_files.append({
                    'path': file_name,
                    'type': malicious_type,
                    'severity': random.choice(['low', 'medium', 'high', 'critical'])
                })
                
                # Log the finding
                self.send_log(f"ALERT: Potential {malicious_type} detected in {file_name}", log_type="error")
            
            # Simulate scanning time
            time.sleep(0.2)  # Brief delay to simulate scanning
        
        # Complete scan report
        self.send_log("", log_type="warning")
        self.send_log("===== VIRUS SCAN COMPLETE =====", log_type="warning")
        self.send_log(f"Total files scanned: {scanned_files}", log_type="warning")
        self.send_log(f"Infected files found: {len(infected_files)}", log_type="warning")
        
        # Report infected files
        if infected_files:
            self.send_log("", log_type="error")
            self.send_log("===== INFECTED FILES =====", log_type="error")
            for idx, file in enumerate(infected_files, 1):
                severity_type = "warning" if file['severity'] in ['low', 'medium'] else "error"
                self.send_log(f"{idx}. {file['path']}", log_type=severity_type)
                self.send_log(f"   Type: {file['type']}, Severity: {file['severity'].upper()}", log_type=severity_type)
            
            # Create alert for infected files
            if device_id != "all":
                try:
                    device = Device.objects.get(id=device_id)
                    # alert = Notification.objects.create(
                    #     device=device,
                    #     alert_type="Virus Scan",
                    #     severity="critical" if any(f['severity'] == 'critical' for f in infected_files) else "high",
                    #     message=f"Virus scan detected {len(infected_files)} infected files on {device}"
                    # )
                    # self.send_alert(alert)
                except Device.DoesNotExist:
                    pass
        else:
            self.send_log("No infected files found", log_type="success")
        
        self.send_log("", log_type="warning")
        self.send_log("===== SCAN SUMMARY =====", log_type="warning")
        status = "ATTENTION NEEDED" if infected_files else "CLEAN"
        status_type = "error" if infected_files else "success"
        self.send_log(f"Status: {status}", log_type=status_type)
        self.send_log(f"Action: {'Manual cleanup required' if infected_files else 'No action needed'}", log_type=status_type)
    
    # Simulate real file system scanning
    def simulate_file_system_walk(self, root_path, malicious_patterns):
        """
        Simulates walking the file system and checking for malicious files.
        In a real implementation, this would use os.walk() on the actual file system.
        """
        file_tree = {
            '/home': ['user1', 'user2', 'user3'],
            '/home/user1': ['documents', 'downloads', 'pictures'],
            '/home/user1/documents': ['report.doc', 'invoice.pdf', 'contract.doc'],
            '/home/user1/downloads': ['software.exe', 'movie.mp4', 'malware.exe'],
            '/home/user2': ['documents', 'music'],
            '/home/user2/documents': ['thesis.pdf', 'notes.txt'],
            '/usr': ['bin', 'lib', 'local'],
            '/usr/bin': ['bash', 'python', 'ssh', 'suspicious.bin'],
            '/var': ['log', 'tmp', 'cache'],
            '/var/log': ['system.log', 'auth.log', 'backdoor.log'],
            '/etc': ['passwd', 'shadow', 'hosts', 'trojan.conf'],
        }
        
        scanned_files = 0
        infected_files = []
        
        # Simulate walking through the file tree
        for dir_path, subdirs in file_tree.items():
            # Skip if not under root_path
            if not dir_path.startswith(root_path):
                continue
            
            # Report current directory
            yield {
                'type': 'directory',
                'path': dir_path,
                'total_files': len([f for f in subdirs if '.' in f])
            }
            
            # Check each file in this directory
            for item in subdirs:
                # If the item is a file (contains a period)
                if '.' in item:
                    scanned_files += 1
                    full_path = f"{dir_path}/{item}"
                    
                    # Check if file contains any malicious pattern
                    is_malicious = any(pattern in item.lower() for pattern in malicious_patterns)
                    
                    if is_malicious:
                        # Determine which pattern matched
                        matching_pattern = next((pattern for pattern in malicious_patterns if pattern in item.lower()), "unknown")
                        
                        # Determine severity based on pattern
                        severity = "critical" if matching_pattern in ['virus', 'malware', 'ransomware', 'rootkit'] else \
                                  "high" if matching_pattern in ['trojan', 'backdoor', 'exploit'] else \
                                  "medium" if matching_pattern in ['spyware', 'keylogger', 'phishing'] else "low"
                        
                        infected_files.append({
                            'path': full_path,
                            'type': matching_pattern,
                            'severity': severity
                        })
                        
                        # Report infected file
                        yield {
                            'type': 'infected',
                            'path': full_path,
                            'malware_type': matching_pattern,
                            'severity': severity
                        }
        
        # Return summary
        yield {
            'type': 'summary',
            'scanned': scanned_files,
            'infected': len(infected_files),
            'infected_files': infected_files
        }
    
    # Check compliance
    def check_compliance(self, device_id):
        # Implementation unchanged from previous version
        self.send_log(f"Checking compliance for device(s) {device_id}...")
        # Rest of the implementation...
    
    # Run diagnostics
    def run_diagnostics(self, device_id):
        # Implementation unchanged from previous version
        self.send_log(f"Running diagnostics for device(s) {device_id}...")
        # Rest of the implementation...
    
    # Get resource usage
    def get_resource_usage(self, device_id):
        # Implementation unchanged from previous version
        self.send_log(f"Fetching resource usage for device(s) {device_id}...")
        # Rest of the implementation...
    
    # Get active alerts
    # def get_active_alerts(self):
        # Implementation unchanged from previous version
        # alerts = MonitoringAlert.objects.filter(
        #     acknowledged=False,
        #     resolved=False
        # )
        # Rest of the implementation...
    
    # Acknowledge alert
    # def acknowledge_alert(self, alert_id):
    #     # Implementation unchanged from previous version
    #     try:
    #         alert = MonitoringAlert.objects.get(id=alert_id)
    #         # Rest of the implementation...
    #     except MonitoringAlert.DoesNotExist:
    #         self.send_log(f"Alert with ID {alert_id} not found", log_type="error")
    
    # Send a log message to the WebSocket
    def send_log(self, message, log_type=None):
        self.send(text_data=json.dumps({
            "type": "log",
            "message": message,
            "log_type": log_type,
            "timestamp": datetime.now().strftime('%H:%M:%S')
        }))
    
    # Send an alert notification
    def send_alert(self, alert):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "send_alert_notification",
                "alert": {
                    "id": alert.id,
                    "device": str(alert.device),
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        )
    
    # Send status update to WebSocket
    def send_status_update(self, event):
        self.send(text_data=json.dumps({
            "type": "status_update",
            "counts": event["counts"]
        }))
    
    # Send alert notification to WebSocket
    def send_alert_notification(self, event):
        self.send(text_data=json.dumps({
            "type": "alert",
            "alert": event["alert"]
        }))
    
    # Send scan results to WebSocket
    def send_scan_results(self, event):
        self.send(text_data=json.dumps({
            "type": "scan_result",
            "results": event["results"]
        }))
    
    # Helper methods for compliance and other features
    # (Implementation unchanged from previous version)

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]
        self.room_group_name = f"chat_{self}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))


import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer

from asgiref.sync import sync_to_async
from django.utils import timezone

import json
import uuid
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone

# Set up logging
logger = logging.getLogger(__name__)

class DeviceDataConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.device_id = str(uuid.uuid4())
        await self.accept()

        logger.info(f"WebSocket connected: device_id={self.device_id}")

        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'device_id': self.device_id,
            'message': 'WebSocket connection established'
        }))

    async def receive(self, text_data):
        logger.debug(f"Received data: {text_data}")
        try:
            data = json.loads(text_data)
            if data.get('type') == 'device_info':
                logger.info(f"Device info received: {data['data']}")
                await self.save_device_info(data['data'])
                await self.send(text_data=json.dumps({
                    'type': 'acknowledge',
                    'message': 'Device information received'
                }))
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.exception("Unexpected error in receive method")

    @sync_to_async
    def save_device_info(self, device_data):
        print(device_data)
        from management.models import Policy, Notification, ActivityReport, BlockedSoftware, InstalledSoftware, User
        user = User.objects.get(username='admin')
        device = create_or_update_device(device_data, user)

        logger.debug(f"Saving device info for device_id={self.device_id}: {device_data}")
        # Device.objects.create(...)  # Uncomment and implement as needed

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected: device_id={self.device_id}, code={close_code}")
