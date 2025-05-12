import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
import random
# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Optional: Add console handler if not already configured globally
console_handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s:%(name)s: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class MonitoringConsumer(AsyncWebsocketConsumer):
    # Track all connected clients with their UUIDs
    connected_clients = {}  # Format: {uuid: client_instance}

    # List of malicious file patterns for scanning
    malicious_patterns = [
        'virus', 'malware', 'trojan', 'backdoor', 'rootkit', 'keylogger',
        'ransomware', 'spyware', 'adware', 'worm', 'exploit', 'hack',
        'suspicious', 'danger', 'unsafe', 'blocked', 'unwanted', 'phishing',
        'crypto-miner', 'botnet'
    ]

    async def connect(self):
        await self.accept()

        # Generate a unique UUID for this connection
        self.client_uuid = str(uuid.uuid4())
        self.connected_clients[self.client_uuid] = self

        # Create room group for broadcasting
        self.room_group_name = "monitoring_dashboard"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        logger.info(
            f"New WebSocket connection accepted. UUID: {self.client_uuid}. "
            f"Total clients: {len(self.connected_clients)}"
        )

        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Monitoring connection established",
            "client_uuid": self.client_uuid,
            "timestamp": datetime.now().isoformat()
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'client_uuid') and self.client_uuid in self.connected_clients:
            del self.connected_clients[self.client_uuid]
            logger.info(
                f"WebSocket disconnected. UUID: {self.client_uuid}, "
                f"code: {close_code}. Remaining clients: {len(self.connected_clients)}"
            )

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @classmethod
    async def broadcast_command(cls, command):
        """Send a command to all connected clients"""
        for client_uuid, client in cls.connected_clients.items():
            try:
                await client.send_command(command)
                logger.debug(f"Command sent to client {client_uuid}")
            except Exception as e:
                logger.error(f"Failed to send command to client {client_uuid}: {str(e)}")

    @classmethod
    async def send_command_to_device(cls, client_uuid, command):
        """Send a command to a specific device by UUID"""
        if client_uuid in cls.connected_clients:
            try:
                await cls.connected_clients[client_uuid].send_command(command)
                logger.debug(f"Command sent to client {client_uuid}")
                return True
            except Exception as e:
                logger.error(f"Failed to send command to client {client_uuid}: {str(e)}")
                return False
        else:
            logger.warning(f"Client UUID {client_uuid} not found in connected clients")
            return False

    async def receive(self, text_data):
        logger.debug(f"Received raw data from {getattr(self, 'client_uuid', 'unknown')}: {text_data}")
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")

            if msg_type == "system_properties":
                await self.handle_system_data(data)
            elif msg_type == "command_response":
                await self.handle_command_response(data)
            elif msg_type == "command":
                await self.process_command(data)
            elif msg_type == "acknowledge_alert":
                await self.acknowledge_alert(data.get("alert_id"))
            else:
                logger.warning(f"Unknown message type received from {self.client_uuid}: {msg_type}")
                await self.send_error("Unknown message type", msg_type)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from {self.client_uuid}: {e}")
            await self.send_error("Invalid JSON received")

    async def handle_system_data(self, data):
        """Handle incoming system monitoring data"""
        timestamp = data.get("timestamp")
        properties = data.get("properties", {})
        logger.info(f"Received system data from {self.client_uuid} at {timestamp}")

        # Here you would typically store the data in your database
        # or process it further

        await self.send(text_data=json.dumps({
            "type": "acknowledge",
            "message": "System data received",
            "client_uuid": self.client_uuid,
            "timestamp": datetime.now().isoformat(),
            "original_timestamp": timestamp
        }))

    async def handle_command_response(self, data):
        """Handle response from executed command"""
        command_id = data.get("command_id")
        output = data.get("output", {})
        timestamp = data.get("timestamp")

        logger.info(
            f"Received command response from {self.client_uuid} for ID {command_id}\n"
            f"Status: {'Success' if output.get('success') else 'Failed'}\n"
            f"Return code: {output.get('returncode')}"
        )

        # Store or process the command response as needed
        # For example, save to database or trigger other actions

    async def process_command(self, data):
        """Process monitoring commands"""
        command = data.get("command", "").strip().lower()
        device_id = data.get("device_id", "all")

        if not command:
            await self.send_error("No command provided")
            return

        command_parts = command.split()
        base_command = command_parts[0]

        # Help command
        if base_command == "help":
            await self.send_log("Available commands:")
            await self.send_log("  status [device_id|all] - Show status of device(s)")
            await self.send_log("  scan [device_id|all] - Run virus scan on device(s)")
            await self.send_log("  compliance [device_id|all] - Check compliance of device(s)")
            await self.send_log("  diagnostics [device_id|all] - Run diagnostics on device(s)")
            await self.send_log("  usage [device_id|all] - Show resource usage")
            await self.send_log("  alerts - Show active alerts")
            await self.send_log("  help - Show this help message")
            await self.send_log("  clear - Clear terminal")

        # Status command
        elif base_command == "status":
            await self.get_device_status(device_id)

        # Scan command
        elif base_command == "scan":
            params = command_parts[1:] if len(command_parts) > 1 else []
            await self.run_virus_scan(device_id, params)

        # Compliance command
        elif base_command == "compliance":
            await self.check_compliance(device_id)

        # Diagnostics command
        elif base_command == "diagnostics":
            await self.run_diagnostics(device_id)

        # Usage command
        elif base_command == "usage":
            await self.get_resource_usage(device_id)

        # Alerts command
        elif base_command == "alerts":
            await self.get_active_alerts()

        # Unknown command
        else:
            await self.send_log(f"Unknown command: {command}", log_type="error")

    async def get_device_status(self, device_id):
        """Get status of one or all devices"""
        if device_id == "all":
            await self.send_log("Fetching status for all devices...")
            # Simulate getting status for all devices
            status = {
                "online": random.randint(1, 10),
                "offline": random.randint(0, 2),
                "warning": random.randint(0, 3),
                "critical": random.randint(0, 1)
            }
            await self.send(text_data=json.dumps({
                "type": "status_report",
                "device_id": "all",
                "status": status,
                "timestamp": datetime.now().isoformat()
            }))
        else:
            await self.send_log(f"Fetching status for device {device_id}...")
            # Simulate getting status for a specific device
            status = {
                "cpu_usage": random.randint(1, 100),
                "memory_usage": random.randint(1, 100),
                "disk_usage": random.randint(1, 100),
                "status": random.choice(["online", "offline", "degraded"]),
                "last_seen": (datetime.now() - timedelta(minutes=random.randint(0, 60))).isoformat()
            }
            await self.send(text_data=json.dumps({
                "type": "status_report",
                "device_id": device_id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }))

    async def run_virus_scan(self, device_id, params=None):
        """Run virus scan simulation"""
        await self.send_log(f"Initiating virus scan on device(s) {device_id}...", log_type="warning")

        # Set scan path
        scan_path = "/"
        if params and len(params) > 0 and params[0] != "all":
            scan_path = params[0]

        await self.send_log(f"Starting file system scan from {scan_path}", log_type="warning")
        await self.send_log(f"Scanning for malicious patterns...", log_type="warning")

        # Simulate scanning
        scanned_files = 0
        infected_files = []

        # Simulate scanning different directories
        directories_to_simulate = [
            '/home', '/usr', '/var', '/etc', '/tmp', '/opt',
            '/mnt', '/media', '/srv', '/bin', '/sbin', '/lib'
        ]

        for dir_path in directories_to_simulate:
            # Simulate scanning this directory
            await self.send_log(f"Scanning directory: {dir_path}")

            # Simulate files being scanned
            num_files = random.randint(10, 100)
            scanned_files += num_files

            # Update progress
            await self.send_log(f"Scanned {num_files} files in {dir_path}, total scanned: {scanned_files}")

            # Randomly find infected files
            if random.random() < 0.3:  # 30% chance to find infected file
                file_name = f"{dir_path}/{random.choice(['file', 'doc', 'exe', 'zip', 'bin', 'sh', 'py'])}_" + \
                            f"{random.randint(1, 999)}.{random.choice(['exe', 'dll', 'sh', 'py', 'bin', 'dat'])}"

                malicious_type = random.choice(self.malicious_patterns)

                infected_files.append({
                    'path': file_name,
                    'type': malicious_type,
                    'severity': random.choice(['low', 'medium', 'high', 'critical'])
                })

                await self.send_log(f"ALERT: Potential {malicious_type} detected in {file_name}", log_type="error")

            # Brief delay to simulate scanning
            await asyncio.sleep(0.2)

        # Complete scan report
        await self.send_log("", log_type="warning")
        await self.send_log("===== VIRUS SCAN COMPLETE =====", log_type="warning")
        await self.send_log(f"Total files scanned: {scanned_files}", log_type="warning")
        await self.send_log(f"Infected files found: {len(infected_files)}", log_type="warning")

        if infected_files:
            await self.send_log("", log_type="error")
            await self.send_log("===== INFECTED FILES =====", log_type="error")
            for idx, file in enumerate(infected_files, 1):
                severity_type = "warning" if file['severity'] in ['low', 'medium'] else "error"
                await self.send_log(f"{idx}. {file['path']}", log_type=severity_type)
                await self.send_log(f"   Type: {file['type']}, Severity: {file['severity'].upper()}",
                                    log_type=severity_type)
        else:
            await self.send_log("No infected files found", log_type="success")

        await self.send_log("", log_type="warning")
        await self.send_log("===== SCAN SUMMARY =====", log_type="warning")
        status = "ATTENTION NEEDED" if infected_files else "CLEAN"
        status_type = "error" if infected_files else "success"
        await self.send_log(f"Status: {status}", log_type=status_type)
        await self.send_log(f"Action: {'Manual cleanup required' if infected_files else 'No action needed'}",
                            log_type=status_type)

    async def check_compliance(self, device_id):
        """Check compliance status"""
        await self.send_log(f"Checking compliance for device(s) {device_id}...")

        # Simulate compliance checks
        checks = [
            {"name": "Password Policy", "status": random.choice(["compliant", "non-compliant"])},
            {"name": "Firewall Enabled", "status": random.choice(["compliant", "non-compliant"])},
            {"name": "Encryption Enabled", "status": random.choice(["compliant", "non-compliant"])},
            {"name": "Automatic Updates", "status": random.choice(["compliant", "non-compliant"])},
            {"name": "Logging Enabled", "status": random.choice(["compliant", "non-compliant"])},
        ]

        compliant_count = sum(1 for check in checks if check["status"] == "compliant")
        compliance_percentage = int((compliant_count / len(checks)) * 100)

        await self.send_log(f"Compliance Score: {compliance_percentage}%",
                            log_type="success" if compliance_percentage > 80 else
                            "warning" if compliance_percentage > 50 else "error")

        for check in checks:
            await self.send_log(f"{check['name']}: {check['status'].upper()}",
                                log_type="success" if check["status"] == "compliant" else "error")

        await self.send_log("Compliance check completed", log_type="warning")

    async def run_diagnostics(self, device_id):
        """Run diagnostics checks"""
        await self.send_log(f"Running diagnostics for device(s) {device_id}...")

        # Simulate diagnostic tests
        tests = [
            {"name": "Connectivity Test", "status": random.choice(["passed", "failed"])},
            {"name": "Disk Health Check", "status": random.choice(["passed", "failed"])},
            {"name": "Memory Test", "status": random.choice(["passed", "failed"])},
            {"name": "CPU Performance", "status": random.choice(["passed", "failed"])},
            {"name": "Service Status", "status": random.choice(["passed", "failed"])},
        ]

        for test in tests:
            await self.send_log(f"Running {test['name']}...")
            await asyncio.sleep(0.5)
            await self.send_log(f"{test['name']}: {test['status'].upper()}",
                                log_type="success" if test["status"] == "passed" else "error")

        passed_count = sum(1 for test in tests if test["status"] == "passed")
        health_percentage = int((passed_count / len(tests)) * 100)

        await self.send_log(f"Device Health: {health_percentage}%",
                            log_type="success" if health_percentage > 80 else
                            "warning" if health_percentage > 50 else "error")
        await self.send_log("Diagnostics completed", log_type="warning")

          # Make sure this is at the top of your file

        async def get_resource_usage(self, device_id):
            """Get resource usage information for a device"""
            await self.send_log(f"Fetching resource usage for device(s): {device_id}...")

            # Simulated resource usage data
            usage_data = {
                "cpu_usage": random.randint(1, 100),
                "memory_usage": random.randint(1, 100),
                "disk_usage": random.randint(1, 100),
                "network_in": random.randint(100, 10000),  # in KB/s
                "network_out": random.randint(100, 10000),  # in KB/s
                "process_count": random.randint(20, 200),
                "uptime": f"{random.randint(1, 30)} days, {random.randint(0, 23)} hours"
            }

            # Log CPU usage with appropriate severity
            cpu_level = "error" if usage_data['cpu_usage'] > 90 else \
                "warning" if usage_data['cpu_usage'] > 70 else "success"
            await self.send_log(f"CPU Usage: {usage_data['cpu_usage']}%", log_type=cpu_level)

            # Log Memory usage
            mem_level = "error" if usage_data['memory_usage'] > 90 else \
                "warning" if usage_data['memory_usage'] > 70 else "success"
            await self.send_log(f"Memory Usage: {usage_data['memory_usage']}%", log_type=mem_level)

            # Log Disk usage
            disk_level = "error" if usage_data['disk_usage'] > 90 else \
                "warning" if usage_data['disk_usage'] > 70 else "success"
            await self.send_log(f"Disk Usage: {usage_data['disk_usage']}%", log_type=disk_level)

            # Log Network I/O, Processes, and Uptime
            await self.send_log(f"Network: IN {usage_data['network_in']} KB/s, OUT {usage_data['network_out']} KB/s")
            await self.send_log(f"Processes Running: {usage_data['process_count']}")
            await self.send_log(f"Uptime: {usage_data['uptime']}")

            return usage_data

        async def get_active_alerts(self):
            """Get active alerts"""
            await self.send_log("Fetching active alerts...")

            # Simulate alerts
            alerts = [
                {
                    "id": str(uuid.uuid4()),
                    "device": f"Device-{random.randint(1, 100)}",
                    "type": random.choice(["CPU", "Memory", "Disk", "Network", "Security"]),
                    "severity": random.choice(["low", "medium", "high", "critical"]),
                    "message": random.choice([
                        "High CPU usage detected",
                        "Memory threshold exceeded",
                        "Disk space running low",
                        "Network latency high",
                        "Suspicious activity detected"
                    ]),
                    "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat()
                } for _ in range(random.randint(0, 5))
            ]

            if not alerts:
                await self.send_log("No active alerts", log_type="success")
                return

            await self.send_log(f"Found {len(alerts)} active alerts:", log_type="warning")

            for alert in alerts:
                severity_type = "warning" if alert["severity"] in ["low", "medium"] else "error"
                await self.send_log(f"[{alert['type'].upper()}] {alert['message']}", log_type=severity_type)
                await self.send_log(f"   Device: {alert['device']}, Severity: {alert['severity'].upper()}, "
                                    f"Time: {alert['timestamp']}", log_type=severity_type)

        async def acknowledge_alert(self, alert_id):
            """Acknowledge an alert"""
            if not alert_id:
                await self.send_error("No alert ID provided")
                return

            await self.send_log(f"Acknowledging alert {alert_id}...")
            # In a real implementation, you would update the alert status in your database
            await self.send_log(f"Alert {alert_id} acknowledged", log_type="success")

        async def send_error(self, message, details=None):
            """Send error message to client"""
            error_msg = {
                "type": "error",
                "message": message,
                "client_uuid": getattr(self, 'client_uuid', 'unknown'),
                "timestamp": datetime.now().isoformat()
            }
            if details:
                error_msg["details"] = details
            await self.send(text_data=json.dumps(error_msg))

        async def send_command(self, command):
            """Send command to client for execution"""
            if not isinstance(command, str):
                raise ValueError("Command must be a string")

            command_id = str(uuid.uuid4())
            command_msg = {
                "type": "command",
                "command_id": command_id,
                "command": command,
                "target_client": self.client_uuid,
                "timestamp": datetime.now().isoformat()
            }

            await self.send(text_data=json.dumps(command_msg))
            return command_id

        async def send_log(self, message, log_type=None):
            """Send log message to client"""
            log_msg = {
                "type": "log",
                "message": message,
                "log_type": log_type,
                "timestamp": datetime.now().isoformat()
            }
            await self.send(text_data=json.dumps(log_msg))

        # Channel layer handlers
        async def send_alert_notification(self, event):
            """Send alert notification to WebSocket"""
            await self.send(text_data=json.dumps({
                "type": "alert",
                "alert": event["alert"]
            }))

        async def send_status_update(self, event):
            """Send status update to WebSocket"""
            await self.send(text_data=json.dumps({
                "type": "status_update",
                "counts": event["counts"]
            }))

        async def send_scan_results(self, event):
            """Send scan results to WebSocket"""
            await self.send(text_data=json.dumps({
                "type": "scan_result",
                "results": event["results"]
            }))