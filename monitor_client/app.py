import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import datetime
import threading

import socket
import subprocess
import re
import uuid
import json
import logging
import platform
import psutil
import asyncio
import websockets
import time
import curses
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
API_HOST = '127.0.0.1:8000'
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('device_info_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DeviceInfoCollector:
    def __init__(self):
        logger.info("Initializing DeviceInfoCollector")
        self.system_info = {
            'hostname': self.get_hostname(),
            'ip_address': self.get_ip_address(),
            'mac_address': self.get_mac_address(),
            'os_info': self.get_os_info(),
            'serial_number': self.get_serial_number(),
            'installed_software': self.get_installed_software(),
            'system_manufacturer': self.get_system_manufacturer(),
            'system_model': self.get_system_model(),
            'performance_metrics': self.get_system_performance(),
            'timestamp': datetime.now().isoformat()
        }
        logger.info("Device information collected successfully")

    def get_hostname(self) -> str:
        """Get the device hostname (works on all OSes)"""
        try:
            hostname = socket.gethostname()
            logger.debug(f"Retrieved hostname: {hostname}")
            return hostname
        except Exception as e:
            logger.error(f"Error getting hostname: {e}")
            return "unknown"

    def get_ip_address(self) -> str:
        """Get the primary IP address (works on all OSes)"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
            logger.debug(f"Retrieved IP address: {ip_address}")
            return ip_address
        except Exception as e:
            logger.error(f"Error getting IP address: {e}")
            return "127.0.0.1"

    def get_mac_address(self) -> str:
        """Get the MAC address (works on all OSes)"""
        try:
            mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
            logger.debug(f"Retrieved MAC address: {mac}")
            return mac
        except Exception as e:
            logger.error(f"Error getting MAC address: {e}")
            return "00:00:00:00:00:00"

    def get_os_info(self) -> Dict[str, str]:
        """Get operating system information (works on all OSes)"""
        try:
            os_info = {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            }
            logger.debug(f"Retrieved OS info: {os_info}")
            return os_info
        except Exception as e:
            logger.error(f"Error getting OS info: {e}")
            return {
                'system': 'unknown',
                'release': 'unknown',
                'version': 'unknown',
                'machine': 'unknown',
                'processor': 'unknown'
            }

    def get_serial_number(self) -> Optional[str]:
        """Get system serial number (OS-specific)"""
        os_type = platform.system().lower()
        logger.info(f"Getting serial number for OS: {os_type}")

        try:
            if os_type == 'windows':
                result = subprocess.check_output("wmic bios get serialnumber", shell=True)
                serial = result.decode().split("\n")[1].strip()
            elif os_type == 'linux':
                result = subprocess.check_output("sudo dmidecode -s system-serial-number", shell=True)
                serial = result.decode().strip()
            elif os_type == 'darwin':  # macOS
                result = subprocess.check_output("ioreg -l | grep IOPlatformSerialNumber", shell=True)
                serial = result.decode().split('=')[-1].strip().strip('"')
            else:
                logger.warning(f"Unsupported OS type: {os_type}")
                return None

            return serial if serial else None

        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting serial number: {e}")
            return None

    def _get_system_info(self) -> Tuple[Optional[str], Optional[str]]:
        """Internal method to get both manufacturer and model (OS-specific)"""
        os_type = platform.system().lower()
        logger.info(f"Getting system info for OS: {os_type}")

        try:
            if os_type == 'windows':
                manufacturer = subprocess.check_output(
                    "wmic computersystem get manufacturer", shell=True
                ).decode().split("\n")[1].strip()
                model = subprocess.check_output(
                    "wmic computersystem get model", shell=True
                ).decode().split("\n")[1].strip()
                return manufacturer, model

            elif os_type == 'linux':
                with open("/sys/devices/virtual/dmi/id/sys_vendor", "r") as f:
                    manufacturer = f.read().strip()
                with open("/sys/devices/virtual/dmi/id/product_name", "r") as f:
                    model = f.read().strip()
                return manufacturer, model

            elif os_type == 'darwin':
                manufacturer = "Apple"
                model = subprocess.check_output(
                    ["sysctl", "-n", "hw.model"]
                ).decode().strip()
                return manufacturer, model

            else:
                logger.warning("Unsupported OS")
                return None, None

        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return None, None

    def get_system_manufacturer(self) -> Optional[str]:
        """Get system manufacturer"""
        manufacturer, _ = self._get_system_info()
        return manufacturer

    def get_system_model(self) -> Optional[str]:
        """Get system model"""
        _, model = self._get_system_info()
        return model
    def get_installed_software(self) -> List[Dict[str, str]]:
        """Get installed software (OS-specific)"""
        os_type = platform.system().lower()
        logger.info(f"Getting installed software for OS: {os_type}")

        try:
            if os_type == 'windows':
                return self._get_windows_software()
            elif os_type == 'linux':
                return self._get_linux_software()
            elif os_type == 'darwin':
                return self._get_macos_software()
            return []
        except Exception as e:
            logger.error(f"Error getting installed software: {e}")
            return []

    def get_system_performance(self) -> Dict[str, Union[float, List[Dict[str, float]]]]:
        """
        Collect comprehensive system performance metrics including:
        - CPU usage (overall and per-core)
        - Memory usage (total, available, used, percentage)
        - Disk usage (total, used, free, percentage for all partitions)
        - Network I/O (bytes sent/received, packets sent/received)
        - System uptime
        - Temperatures (if available)
        - Battery status (if available)

        Returns:
            dict: Dictionary containing all performance metrics
        """
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {},
            'memory': {},
            'disks': [],
            'network': {},
            'system': {}
        }

        try:
            # CPU Metrics
            cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
            metrics['cpu'] = {
                'overall_usage': sum(cpu_usage) / len(cpu_usage),
                'per_core_usage': cpu_usage,
                'core_count': psutil.cpu_count(logical=True),
                'frequency': psutil.cpu_freq().current if hasattr(psutil, 'cpu_freq') else None,
                'model': platform.processor()
            }

            # Memory Metrics
            mem = psutil.virtual_memory()
            metrics['memory'] = {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'free': mem.free,
                'percent': mem.percent,
                'swap_total': psutil.swap_memory().total,
                'swap_used': psutil.swap_memory().used,
                'swap_free': psutil.swap_memory().free,
                'swap_percent': psutil.swap_memory().percent
            }

            # Disk Metrics
            for partition in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    metrics['disks'].append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    })
                except Exception as e:
                    logger.warning(f"Could not get disk usage for {partition.mountpoint}: {e}")

            # Network Metrics
            net_io = psutil.net_io_counters()
            metrics['network'] = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout,
                'dropin': net_io.dropin,
                'dropout': net_io.dropout
            }

            # System Metrics
            metrics['system']['uptime'] = psutil.boot_time()

            # Temperatures (if available)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    metrics['system']['temperatures'] = temps
            except AttributeError:
                pass

            # Battery (if available)
            try:
                battery = psutil.sensors_battery()
                if battery:
                    metrics['system']['battery'] = {
                        'percent': battery.percent,
                        'power_plugged': battery.power_plugged,
                        'secsleft': battery.secsleft
                    }
            except AttributeError:
                pass

            logger.debug("System performance metrics collected successfully")
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")

        return metrics

    def get_running_processes(self, top_n: int = 10) -> List[Dict[str, Union[str, float]]]:
        """Get top running processes by CPU usage"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'],
                        'memory': proc.info['memory_percent'],
                        'status': proc.info['status']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by CPU usage and get top N
            processes.sort(key=lambda p: p['cpu'], reverse=True)
            return processes[:top_n]
        except Exception as e:
            logger.error(f"Error getting running processes: {e}")
            return []

    def kill_process(self, pid: int) -> bool:
        """Attempt to kill a process by PID"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            return True
        except Exception as e:
            logger.error(f"Error killing process {pid}: {e}")
            return False

    def get_active_alerts(self) -> List[Dict[str, str]]:
        """Generate system alerts based on current performance"""
        alerts = []
        perf = self.get_system_performance()

        # Memory alert
        if perf['memory']['percent'] > 85:
            alerts.append({
                'type': 'Elevated Memory Usage',
                'message': f"Memory usage is at {perf['memory']['percent']:.1f}%",
                'timestamp': datetime.now().strftime("%I:%M:%S %p")
            })

        # CPU alert
        if perf['cpu']['overall_usage'] > 90:
            alerts.append({
                'type': 'High CPU Usage',
                'message': f"CPU usage is at {perf['cpu']['overall_usage']:.1f}%",
                'timestamp': datetime.now().strftime("%I:%M:%S %p")
            })

        # Disk alert
        for disk in perf['disks']:
            if disk['percent'] > 80:
                alerts.append({
                    'type': 'Disk Space Warning',
                    'message': f"Disk usage ({disk['mountpoint']}) is at {disk['percent']:.1f}%",
                    'timestamp': datetime.now().strftime("%I:%M:%S %p")
                })
                break

        return alerts

    def get_network_speed(self) -> Tuple[float, float]:
        """Get current network download/upload speeds in MB/s"""
        try:
            io1 = psutil.net_io_counters()
            time.sleep(1)
            io2 = psutil.net_io_counters()

            download = (io2.bytes_recv - io1.bytes_recv) / (1024 * 1024)  # MB/s
            upload = (io2.bytes_sent - io1.bytes_sent) / (1024 * 1024)  # MB/s
            return download, upload
        except Exception as e:
            logger.error(f"Error getting network speed: {e}")
            return 0.0, 0.0

    def display_live_dashboard(self, refresh_interval: int = 2):
        """Display a live updating system dashboard"""
        try:
            # Initialize curses
            stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            stdscr.keypad(True)

            # Enable color if available
            if curses.has_colors():
                curses.start_color()
                curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
                curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
                curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
                curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

            try:
                while True:
                    stdscr.clear()
                    now = datetime.now()

                    # Get current system info
                    perf = self.get_system_performance()
                    alerts = self.get_active_alerts()
                    processes = self.get_running_processes(10)
                    download, upload = self.get_network_speed()

                    # Header
                    stdscr.addstr(0, 0, f"Connected - Last updated: {now.strftime('%I:%M:%S %p')}", curses.A_BOLD)

                    # System Info
                    stdscr.addstr(2, 0, "System Information:", curses.A_BOLD)
                    stdscr.addstr(3, 2, f"Hostname: {self.system_info['hostname']}")
                    stdscr.addstr(4, 2, f"IP: {self.system_info['ip_address']}")
                    stdscr.addstr(5, 2, f"OS: {self.system_info['os_info']['system']} {self.system_info['os_info']['release']}")

                    # CPU Usage
                    stdscr.addstr(7, 0, "CPU Usage", curses.A_BOLD)
                    stdscr.addstr(7, 12, "Live", curses.color_pair(3) | curses.A_BLINK)
                    cpu_usage = perf['cpu']['overall_usage']
                    cpu_color = curses.color_pair(3)  # Green
                    if cpu_usage > 70:
                        cpu_color = curses.color_pair(2)  # Yellow
                    if cpu_usage > 90:
                        cpu_color = curses.color_pair(1)  # Red
                    stdscr.addstr(8, 2, f"{cpu_usage:.1f}%", cpu_color)
                    stdscr.addstr(9, 2, f"{perf['cpu']['core_count']} cores | {self.system_info['os_info']['processor']}")

                    # Memory Usage
                    stdscr.addstr(11, 0, "Memory Usage", curses.A_BOLD)
                    stdscr.addstr(11, 14, "Live", curses.color_pair(3) | curses.A_BLINK)
                    mem_usage = perf['memory']['percent']
                    mem_color = curses.color_pair(3)  # Green
                    if mem_usage > 70:
                        mem_color = curses.color_pair(2)  # Yellow
                    if mem_usage > 85:
                        mem_color = curses.color_pair(1)  # Red
                    stdscr.addstr(12, 2, f"{mem_usage:.1f}%", mem_color)
                    stdscr.addstr(13, 2, f"{perf['memory']['used'] / (1024**3):.2f} GB / {perf['memory']['total'] / (1024**3):.2f} GB")

                    # Disk Usage
                    stdscr.addstr(15, 0, "Disk Usage", curses.A_BOLD)
                    stdscr.addstr(15, 12, "Live", curses.color_pair(3) | curses.A_BLINK)
                    if perf['disks']:
                        disk = perf['disks'][0]  # Main disk
                        disk_usage = disk['percent']
                        disk_color = curses.color_pair(3)  # Green
                        if disk_usage > 70:
                            disk_color = curses.color_pair(2)  # Yellow
                        if disk_usage > 80:
                            disk_color = curses.color_pair(1)  # Red
                        stdscr.addstr(16, 2, f"{disk_usage:.1f}%", disk_color)
                        stdscr.addstr(17, 2, f"{disk['used'] / (1024**3):.2f} GB / {disk['total'] / (1024**3):.2f} GB")

                    # Network
                    stdscr.addstr(19, 0, "Network", curses.A_BOLD)
                    stdscr.addstr(19, 9, "Live", curses.color_pair(3) | curses.A_BLINK)
                    stdscr.addstr(20, 2, "Download")
                    stdscr.addstr(20, 12, f"{download:.2f} MB/s", curses.color_pair(4))
                    stdscr.addstr(21, 2, "Upload")
                    stdscr.addstr(21, 12, f"{upload:.2f} MB/s", curses.color_pair(4))

                    # Active Alerts
                    stdscr.addstr(23, 0, "Active Alerts", curses.A_BOLD)
                    stdscr.addstr(23, 14, str(len(alerts)), curses.color_pair(1) if alerts else curses.color_pair(3))
                    for i, alert in enumerate(alerts[:3], 1):
                        stdscr.addstr(24 + i, 2, f"{alert['type']}")
                        stdscr.addstr(24 + i, 25, alert['message'], curses.color_pair(2))
                        stdscr.addstr(24 + i, 60, alert['timestamp'])

                    # Running Processes
                    stdscr.addstr(28, 0, "Running Processes", curses.A_BOLD)
                    stdscr.addstr(29, 0, "PID  Name                 CPU    Memory  Status")
                    for i, proc in enumerate(processes[:10], 30):
                        stdscr.addstr(i, 0, f"{proc['pid']:<5} {proc['name'][:20]:<20} {proc['cpu']:>5.1f}% {proc['memory']:>7.1f}% {proc['status']}")

                    stdscr.refresh()
                    time.sleep(refresh_interval)

            except KeyboardInterrupt:
                pass
            finally:
                # Clean up curses
                curses.nocbreak()
                stdscr.keypad(False)
                curses.echo()
                curses.endwin()

        except Exception as e:
            logger.error(f"Error in live dashboard: {e}")
            # Ensure curses is properly cleaned up even on error
            try:
                curses.nocbreak()
                stdscr.keypad(False)
                curses.echo()
                curses.endwin()
            except:
                pass

    # Windows-specific functions
    def _get_windows_serial(self) -> Optional[str]:
        """Get serial number on Windows"""
        try:
            output = subprocess.check_output(
                'wmic bios get serialnumber',
                shell=True,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            serial = output.strip().split('\n')[1]
            result = serial if serial else "Unknown"
            logger.debug(f"Windows serial number: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting Windows serial number: {e}")
            return None

    def _get_windows_manufacturer(self) -> Optional[str]:
        """Get manufacturer on Windows"""
        try:
            output = subprocess.check_output(
                'wmic computersystem get manufacturer',
                shell=True,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            manufacturer = output.strip().split('\n')[1]
            result = manufacturer if manufacturer else "Unknown"
            logger.debug(f"Windows manufacturer: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting Windows manufacturer: {e}")
            return None

    def _get_windows_model(self) -> Optional[str]:
        """Get model on Windows"""
        try:
            output = subprocess.check_output(
                'wmic computersystem get model',
                shell=True,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            model = output.strip().split('\n')[1]
            result = model if model else "Unknown"
            logger.debug(f"Windows model: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting Windows model: {e}")
            return None

    def _get_windows_software(self) -> List[Dict[str, str]]:
        """Get installed software on Windows"""
        software_list = []
        try:
            logger.info("Getting Windows installed software")

            # Get 64-bit programs
            command = [
                'reg', 'query',
                r'HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall',
                '/s'
            ]
            output = subprocess.check_output(
                command,
                shell=True,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Get 32-bit programs on 64-bit Windows
            command_32bit = [
                'reg', 'query',
                r'HKLM\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
                '/s'
            ]
            output += subprocess.check_output(
                command_32bit,
                shell=True,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            current_software = {}
            for line in output.split('\n'):
                if 'REG_SZ' in line:
                    name = line.split('REG_SZ')[0].strip()
                    value = line.split('REG_SZ')[1].strip()
                    if name == 'DisplayName':
                        current_software['name'] = value
                    elif name == 'DisplayVersion':
                        current_software['version'] = value
                    elif name == 'Publisher':
                        current_software['publisher'] = value
                    elif name == 'InstallDate':
                        try:
                            # Try to parse the install date (format is often YYYYMMDD)
                            install_date = datetime.strptime(value, '%Y%m%d').strftime('%Y-%m-%d')
                            current_software['install_date'] = install_date
                        except ValueError:
                            current_software['install_date'] = value
                elif line.startswith('HKEY_') and current_software:
                    software_list.append(current_software)
                    current_software = {}

            if current_software:
                software_list.append(current_software)

            logger.info(f"Found {len(software_list)} installed Windows applications")
        except Exception as e:
            logger.error(f"Error getting Windows software: {e}")

        return software_list

    # Linux-specific functions
    def _get_linux_serial(self) -> Optional[str]:
        """Get serial number on Linux"""
        try:
            commands = [
                'sudo dmidecode -s system-serial-number',
                'cat /sys/class/dmi/id/product_serial',
                'cat /proc/cpuinfo | grep Serial | cut -d " " -f 2'
            ]

            for cmd in commands:
                try:
                    output = subprocess.check_output(
                        cmd,
                        shell=True,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    ).strip()
                    if output and output != "None":
                        logger.debug(f"Linux serial number: {output} (from command: {cmd})")
                        return output
                except Exception as e:
                    logger.debug(f"Command failed: {cmd} - {e}")
                    continue
            logger.warning("Could not determine Linux serial number")
            return "Unknown"
        except Exception as e:
            logger.error(f"Error getting Linux serial number: {e}")
            return None

    def _get_linux_manufacturer(self) -> Optional[str]:
        """Get manufacturer on Linux"""
        try:
            output = subprocess.check_output(
                'cat /sys/class/dmi/id/sys_vendor',
                shell=True,
                stderr=subprocess.PIPE,
                universal_newlines=True
            ).strip()
            result = output if output else "Unknown"
            logger.debug(f"Linux manufacturer: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting Linux manufacturer: {e}")
            return None

    def _get_linux_model(self) -> Optional[str]:
        """Get model on Linux"""
        try:
            output = subprocess.check_output(
                'cat /sys/class/dmi/id/product_name',
                shell=True,
                stderr=subprocess.PIPE,
                universal_newlines=True
            ).strip()
            result = output if output else "Unknown"
            logger.debug(f"Linux model: {result}")
            return result
        except Exception as e:
            logger.error(f"Error getting Linux model: {e}")
            return None

    def _get_linux_software(self) -> List[Dict[str, str]]:
        """Get installed software on Linux"""
        software_list = []

        try:
            logger.info("Getting Linux installed software")

            # Debian/Ubuntu systems (dpkg)
            try:
                output = subprocess.check_output(
                    'dpkg-query -W -f=\'${Package}\t${Version}\t${Maintainer}\t${install-date:date}\n\'',
                    shell=True,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                for line in output.split('\n'):
                    if line.strip():
                        parts = line.split('\t')
                        software = {
                            'name': parts[0],
                            'version': parts[1] if len(parts) > 1 else 'Unknown',
                            'publisher': parts[2] if len(parts) > 2 else 'Unknown'
                        }
                        if len(parts) > 3 and parts[3]:
                            software['install_date'] = parts[3]
                        software_list.append(software)
                logger.debug(f"Found {len(software_list)} packages via dpkg")
            except Exception as e:
                logger.debug(f"dpkg query failed: {e}")

            # RedHat/CentOS systems (rpm)
            try:
                output = subprocess.check_output(
                    'rpm -qa --queryformat "%{NAME}\t%{VERSION}\t%{VENDOR}\t%{INSTALLTIME:date}\n"',
                    shell=True,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                for line in output.split('\n'):
                    if line.strip():
                        parts = line.split('\t')
                        software = {
                            'name': parts[0],
                            'version': parts[1] if len(parts) > 1 else 'Unknown',
                            'publisher': parts[2] if len(parts) > 2 else 'Unknown'
                        }
                        if len(parts) > 3 and parts[3]:
                            software['install_date'] = parts[3]
                        software_list.append(software)
                logger.debug(f"Found {len(software_list)} packages via rpm")
            except Exception as e:
                logger.debug(f"rpm query failed: {e}")

            logger.info(f"Total found {len(software_list)} Linux packages")
        except Exception as e:
            logger.error(f"Error getting Linux software: {e}")

        return software_list

    # macOS-specific functions
    def _get_macos_serial(self) -> Optional[str]:
        """Get serial number on macOS"""
        try:
            output = subprocess.check_output(
                'system_profiler SPHardwareDataType | grep Serial',
                shell=True,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            serial = output.split(':')[-1].strip()
            logger.debug(f"macOS serial number: {serial}")
            return serial
        except Exception as e:
            logger.error(f"Error getting macOS serial number: {e}")
            return None

    def _get_macos_software(self) -> List[Dict[str, str]]:
        """Get installed software on macOS"""
        software_list = []
        try:
            logger.info("Getting macOS installed software")

            # Get applications from /Applications
            try:
                output = subprocess.check_output(
                    'system_profiler SPApplicationsDataType -json',
                    shell=True,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                apps_data = json.loads(output)

                for app_info in apps_data.get('SPApplicationsDataType', []):
                    if isinstance(app_info, dict):
                        software = {
                            'name': app_info.get('_name', 'Unknown'),
                            'version': app_info.get('version', 'Unknown'),
                            'publisher': app_info.get('obtained_from', 'Unknown'),
                            'install_date': app_info.get('lastModified', 'Unknown')
                        }
                        software_list.append(software)
            except Exception as e:
                logger.error(f"Error getting macOS applications: {e}")

            # Get homebrew packages
            try:
                output = subprocess.check_output(
                    'brew list --versions',
                    shell=True,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                for line in output.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            software = {
                                'name': parts[0],
                                'version': parts[1],
                                'publisher': 'Homebrew',
                                'install_date': 'Unknown'
                            }
                            software_list.append(software)
            except Exception as e:
                logger.debug(f"Homebrew not available or failed: {e}")

            logger.info(f"Found {len(software_list)} macOS applications/packages")
        except Exception as e:
            logger.error(f"Error getting macOS software: {e}")

        return software_list

    def to_json(self, indent: int = 2) -> str:
        """Return collected data as JSON"""
        try:
            json_data = json.dumps(self.system_info, indent=indent)
            logger.info("Successfully converted device info to JSON")
            return json_data
        except Exception as e:
            logger.error(f"Error converting device info to JSON: {e}")
            return json.dumps({"error": "Could not serialize device info"})

    def print_info(self):
        """Print collected information in readable format"""
        try:
            print(f"Hostname: {self.system_info['hostname']}")
            print(f"IP Address: {self.system_info['ip_address']}")
            print(f"MAC Address: {self.system_info['mac_address']}")
            print("\nOS Information:")
            for key, value in self.system_info['os_info'].items():
                print(f"  {key.capitalize()}: {value}")

            print(f"\nSerial Number: {self.system_info['serial_number']}")
            print(f"System Manufacturer: {self.system_info['system_manufacturer']}")
            print(f"System Model: {self.system_info['system_model']}")

            # Print performance metrics
            print("\nPerformance Metrics:")
            perf = self.system_info['performance_metrics']
            print(f"  CPU Usage: {perf['cpu']['overall_usage']:.1f}%")
            print(f"  Memory Usage: {perf['memory']['percent']}%")
            print(f"  Disk Usage (main): {perf['disks'][0]['percent'] if perf['disks'] else 'N/A'}%")
            print(f"  Network Sent: {perf['network']['bytes_sent'] / (1024*1024):.2f} MB")
            print(f"  Network Received: {perf['network']['bytes_recv'] / (1024*1024):.2f} MB")

            print("\nInstalled Software (first 10):")
            for i, software in enumerate(self.system_info['installed_software'][:10], 1):
                install_date = software.get('install_date', 'Unknown')
                print(f"  {i}. {software.get('name', 'Unknown')} - Version: {software.get('version', 'Unknown')} - Installed: {install_date}")

            if len(self.system_info['installed_software']) > 10:
                print(f"  ... and {len(self.system_info['installed_software']) - 10} more applications")
        except Exception as e:
            logger.error(f"Error printing device info: {e}")

async def send_device_info(uri, device_info):
    try:
        logger.info(f"Attempting to connect to WebSocket at {uri}")
        async with websockets.connect(uri) as websocket:
            # Wait for connection established message
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            response_data = json.loads(response)
            device_id = response_data.get("device_id")

            # Send device_info
            await websocket.send(json.dumps({
                "type": "device_info",
                "data": device_info
            }))
            logger.info("Device info sent successfully")

            # Wait for acknowledgement
            ack = await websocket.recv()
            logger.info(f"Received acknowledgement: {ack}")
    except Exception as e:
        logger.error(f"Error in WebSocket communication: {e}")


collector = DeviceInfoCollector()
def run_app():
    try:
        logger.info("Starting device information collection")


        # Check for command line arguments
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == "--dashboard":
            collector.display_live_dashboard()
        else:
            collector.print_info()
            device_info = collector.to_json()

            # Save to JSON file
            with open('device_info.json', 'w') as f:
                f.write(device_info)
            logger.info("Device information has been saved to 'device_info.json'")

            # Replace with your WebSocket URL
            websocket_url = f"ws://{API_HOST}/ws/device-tracker/"
            asyncio.run(send_device_info(websocket_url, device_info=device_info))

    except Exception as e:
        logger.error(f"Error in main execution: {e}")

def run_app_threaded():
    thread = threading.Thread(target=run_app)
    thread.daemon = True
    thread.start()
class DeviceInfoUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Device Information Dashboard")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('Status.TLabel', font=('Arial', 10, 'bold'))
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('TNotebook', background='#f0f0f0')
        self.style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'))

        # Create main container
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create header
        self.create_header()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Create tabs
        self.create_local_info_tab()
        self.create_api_info_tab()
        self.create_performance_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            style='Status.TLabel'
        )
        self.status_bar.pack(fill=tk.X, pady=(5, 0))

        # Initialize with local data
        self.update_local_info()
        self.fetch_api_data_threaded() # Fetch API data on initialization
        self.schedule_run_app()
    def schedule_run_app(self):
        run_app_threaded()
        # Schedule next run in 5000 milliseconds (5 seconds)
        self.root.after(5000, self.schedule_run_app)

    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="Device Information Dashboard",
            style='Header.TLabel'
        ).pack(side=tk.LEFT)

        refresh_btn = ttk.Button(
            header_frame,
            text="Refresh All",
            command=self.refresh_all
        )
        refresh_btn.pack(side=tk.RIGHT, padx=(0, 5))

        api_refresh_btn = ttk.Button(
            header_frame,
            text="Refresh API Data",
            command=self.fetch_api_data_threaded
        )
        api_refresh_btn.pack(side=tk.RIGHT, padx=5)

    def create_local_info_tab(self):
        self.local_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.local_tab, text="Local Information")

        # Create paned window for left/right split
        paned = ttk.PanedWindow(self.local_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left pane - Basic info
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="System Information", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))

        self.basic_info_frame = ttk.Frame(left_frame)
        self.basic_info_frame.pack(fill=tk.X, padx=5, pady=5)

        # Right pane - Software list
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Installed Software", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))

        # Treeview for software
        self.software_tree = ttk.Treeview(
            right_frame,
            columns=('name', 'version', 'publisher', 'install_date'),
            show='headings'
        )
        self.software_tree.heading('name', text='Name')
        self.software_tree.heading('version', text='Version')
        self.software_tree.heading('publisher', text='Publisher')
        self.software_tree.heading('install_date', text='Install Date')

        self.software_tree.column('name', width=200)
        self.software_tree.column('version', width=100)
        self.software_tree.column('publisher', width=150)
        self.software_tree.column('install_date', width=100)

        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.software_tree.yview)
        self.software_tree.configure(yscroll=scrollbar.set)

        self.software_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_api_info_tab(self):
        self.api_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.api_tab, text="API Information")

        # Control frame
        control_frame = ttk.Frame(self.api_tab)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(control_frame, text="Enter Hostname:").pack(side=tk.LEFT, padx=(0, 5))
        self.hostname_entry = ttk.Entry(control_frame, width=30)
        self.hostname_entry.pack(side=tk.LEFT, padx=(0, 5))
        fetch_btn = ttk.Button(control_frame, text="Fetch Data", command=self.fetch_api_data_threaded)
        fetch_btn.pack(side=tk.LEFT)

        # API info display frame
        self.api_info_display = ttk.Frame(self.api_tab)
        self.api_info_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Labels for API data
        ttk.Label(self.api_info_display, text="Device Details from API", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))

        self.api_labels = {}
        info_labels = [
            ("Hostname:", "hostname"),
            ("IP Address:", "ip_address"),
            ("Department:", "department"),
            ("OS:", "os"),
            ("Status:", "status"),
            ("Device Type:", "device_type"),
            ("CPU Usage:", "cpu_usage"),
            ("Memory Usage:", "memory_usage"),
            ("Disk Usage:", "disk_usage"),
            ("Download Speed:", "network_download_speed"),
            ("Upload Speed:", "network_upload_speed"),
            ("Last Updated:", "last_updated")
        ]

        for i, (label_text, key) in enumerate(info_labels):
            frame = ttk.Frame(self.api_info_display)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=label_text, width=20, anchor=tk.W).pack(side=tk.LEFT)
            if key == 'status':
                self.api_labels[key] = ttk.Label(frame,  anchor=tk.W)
            else:
                self.api_labels[key] = ttk.Label(frame, text="N/A", anchor=tk.W)

            self.api_labels[key].pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_performance_tab(self):
        self.performance_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.performance_tab, text="Performance Metrics")

        # CPU Usage
        ttk.Label(self.performance_tab, text="CPU Usage", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W,
                                                                                      pady=(0, 5))
        self.cpu_usage = ttk.Label(self.performance_tab, text="0.0%")
        self.cpu_usage.grid(row=1, column=0, sticky=tk.W, padx=5)

        # Memory Usage
        ttk.Label(self.performance_tab, text="Memory Usage", style='Header.TLabel').grid(row=0, column=1, sticky=tk.W,
                                                                                         pady=(0, 5))
        self.memory_usage = ttk.Label(self.performance_tab, text="0.0% (0.0 GB / 0.0 GB)")
        self.memory_usage.grid(row=1, column=1, sticky=tk.W, padx=5)

        # Disk Usage
        ttk.Label(self.performance_tab, text="Disk Usage", style='Header.TLabel').grid(row=0, column=2, sticky=tk.W,
                                                                                       pady=(0, 5))
        self.disk_usage = ttk.Label(self.performance_tab, text="0.0% (0.0 GB / 0.0 GB)")
        self.disk_usage.grid(row=1, column=2, sticky=tk.W, padx=5)

        # Network
        ttk.Label(self.performance_tab, text="Network", style='Header.TLabel').grid(row=2, column=0, sticky=tk.W,
                                                                                    pady=(10, 5))
        self.network_download = ttk.Label(self.performance_tab, text="Download: 0.0 MB/s")
        self.network_download.grid(row=3, column=0, sticky=tk.W, padx=5)
        self.network_upload = ttk.Label(self.performance_tab, text="Upload: 0.0 MB/s")
        self.network_upload.grid(row=4, column=0, sticky=tk.W, padx=5)

        # Alerts
        ttk.Label(self.performance_tab, text="Active Alerts", style='Header.TLabel').grid(row=2, column=1, columnspan=2,
                                                                                          sticky=tk.W, pady=(10, 5))
        self.alerts_text = tk.Text(
            self.performance_tab,
            height=5,
            width=60,
            wrap=tk.WORD,
            font=('Arial', 9),
            padx=5,
            pady=5,
            state=tk.DISABLED
        )
        self.alerts_text.grid(row=3, column=1, columnspan=2, rowspan=2, sticky=tk.W + tk.E, padx=5)

        # Processes
        ttk.Label(self.performance_tab, text="Top Processes", style='Header.TLabel').grid(row=5, column=0, columnspan=3,
                                                                                          sticky=tk.W, pady=(10, 5))

        self.process_tree = ttk.Treeview(
            self.performance_tab,
            columns=('pid', 'name', 'cpu', 'memory', 'status'),
            show='headings',
            height=10
        )
        self.process_tree.heading('pid', text='PID')
        self.process_tree.heading('name', text='Name')
        self.process_tree.heading('cpu', text='CPU %')
        self.process_tree.heading('memory', text='Memory %')
        self.process_tree.heading('status', text='Status')

        self.process_tree.column('pid', width=50)
        self.process_tree.column('name', width=150)
        self.process_tree.column('cpu', width=60)
        self.process_tree.column('memory', width=70)
        self.process_tree.column('status', width=80)

        scrollbar = ttk.Scrollbar(
            self.performance_tab,
            orient=tk.VERTICAL,
            command=self.process_tree.yview
        )
        self.process_tree.configure(yscrollcommand=scrollbar.set)

        self.process_tree.grid(row=6, column=0, columnspan=3, sticky=tk.W + tk.E + tk.N + tk.S)
        scrollbar.grid(row=6, column=3, sticky=tk.N + tk.S)

        # Configure grid weights
        self.performance_tab.columnconfigure(0, weight=1)
        self.performance_tab.columnconfigure(1, weight=1)
        self.performance_tab.columnconfigure(2, weight=1)

    def update_local_info(self):
        try:
            system_info = collector.system_info

            # Clear existing widgets in basic info frame
            for widget in self.basic_info_frame.winfo_children():
                widget.destroy()

            # Add basic info labels
            info_pairs = [
                ("Hostname:", system_info['hostname']),
                ("IP Address:", system_info['ip_address']),
                ("MAC Address:", system_info['mac_address']),
                ("OS:", f"{system_info['os_info']['system']} {system_info['os_info']['release']}"),
                ("System Manufacturer:", system_info['system_manufacturer']),
                ("System Model:", system_info['system_model']),
                ("Serial Number:", system_info['serial_number'])
            ]

            for i, (label, value) in enumerate(info_pairs):
                ttk.Label(self.basic_info_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
                ttk.Label(self.basic_info_frame, text=value).grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)

            # Update software tree
            self.software_tree.delete(*self.software_tree.get_children())
            for software in system_info['installed_software']:
                self.software_tree.insert('', tk.END, values=(
                    software.get('name', 'Unknown'),
                    software.get('version', 'Unknown'),
                    software.get('publisher', 'Unknown'),
                    software.get('install_date', 'Unknown')
                ))

            # Update performance metrics
            self.update_performance_metrics(system_info['performance_metrics'])

            # Set hostname in API tab if empty
            if not self.hostname_entry.get():
                self.hostname_entry.insert(0, system_info['hostname'])

            self.status_var.set("Local information updated successfully")
        except Exception as e:
            self.status_var.set(f"Error updating local info: {str(e)}")
            messagebox.showerror("Error", f"Failed to update local information:\n{str(e)}")

    def update_performance_metrics(self, perf_metrics):
        try:
            # CPU
            cpu_usage = perf_metrics['cpu']['overall_usage']
            self.cpu_usage.config(text=f"{cpu_usage:.1f}%")

            # Memory
            mem = perf_metrics['memory']
            mem_text = f"{mem['percent']:.1f}% ({mem['used'] / (1024 ** 3):.1f} GB / {mem['total'] / (1024 ** 3):.1f} GB)"
            self.memory_usage.config(text=mem_text)

            # Disk
            if perf_metrics['disks']:
                disk = perf_metrics['disks'][0]
                disk_text = f"{disk['percent']:.1f}% ({disk['used'] / (1024 ** 3):.1f} GB / {disk['total'] / (1024 ** 3):.1f} GB)"
                self.disk_usage.config(text=disk_text)

            # Network
            net_io = perf_metrics['network']
            download_speed = net_io['bytes_recv'] / (1024 * 1024)  # MB
            upload_speed = net_io['bytes_sent'] / (1024 * 1024)  # MB
            self.network_download.config(text=f"Download: {download_speed:.2f} MB")
            self.network_upload.config(text=f"Upload: {upload_speed:.2f} MB")

            # Alerts
            alerts = collector.get_active_alerts()
            self.alerts_text.config(state=tk.NORMAL)
            self.alerts_text.delete(1.0, tk.END)

            if alerts:
                for alert in alerts:
                    self.alerts_text.insert(tk.END, f"⚠ {alert['type']}: {alert['message']}\n")
                self.alerts_text.tag_config("alert", foreground="red")
            else:
                self.alerts_text.insert(tk.END, "No active alerts")
                self.alerts_text.tag_config("normal", foreground="green")

            self.alerts_text.config(state=tk.DISABLED)

            # Processes
            self.process_tree.delete(*self.process_tree.get_children())
            processes = collector.get_running_processes(10)
            for proc in processes:
                self.process_tree.insert('', tk.END, values=(
                    proc['pid'],
                    proc['name'],
                    f"{proc['cpu']:.1f}",
                    f"{proc['memory']:.1f}",
                    proc['status']
                ))

        except Exception as e:
            self.status_var.set(f"Error updating performance metrics: {str(e)}")

    def fetch_api_data_threaded(self):
        """Start API fetch in a separate thread to prevent UI freezing"""
        self.status_var.set("Fetching API data...")
        threading.Thread(target=self.fetch_api_data, daemon=True).start()

    def fetch_api_data(self):
        try:
            hostname = self.hostname_entry.get().strip()
            if not hostname:
                messagebox.showwarning("Warning", "Please enter a hostname")
                return

            # Simulate API call (replace with actual API call)
            api_url = f"http://{API_HOST}/api/devices/by-hostname/{hostname}/"
            response = requests.get(api_url).json()

            # Define status color mapping
            status_colors = {
                "compliant": "green",
                "Compliant": "green",
                "non-compliant": "red",
                "Non-Compliant": "red",
                "warning": "orange",
                "Warning": "orange"
            }

            # Update the API labels with the fetched data
            if response:
                self.api_labels['hostname'].config(text=response.get('hostname', 'N/A'))
                self.api_labels['ip_address'].config(text=response.get('ip_address', 'N/A'))
                self.api_labels['department'].config(text=response.get('department', 'N/A'))
                self.api_labels['os'].config(text=response.get('os', 'N/A'))

                status = response.get('status', 'N/A')
                self.api_labels['status'].config(text=status)
                self.api_labels['status'].config(foreground=status_colors.get(status, 'black'))

                self.api_labels['device_type'].config(text=response.get('device_type', 'N/A'))
                self.api_labels['cpu_usage'].config(text=f"{response.get('cpu_usage', 0.0):.2f}%")
                self.api_labels['memory_usage'].config(text=f"{response.get('memory_usage', 0.0):.2f}%")
                self.api_labels['disk_usage'].config(text=f"{response.get('disk_usage', 0.0):.2f}%")
                self.api_labels['network_download_speed'].config(text=f"{response.get('network_download_speed', 0.0):.2f} MB/s")
                self.api_labels['network_upload_speed'].config(text=f"{response.get('network_upload_speed', 0.0):.2f} MB/s")
                self.api_labels['last_updated'].config(text=response.get('last_updated', 'N/A'))

                self.status_var.set(f"API data fetched successfully for {hostname}")
            else:
                self.status_var.set(f"No data found for hostname: {hostname}")
                messagebox.showinfo("Info", f"No data found for hostname: {hostname}")

        except requests.exceptions.RequestException as e:
            self.status_var.set(f"Error fetching API data: {str(e)}")
            messagebox.showerror("Error", f"Failed to fetch API data:\n{str(e)}")
        except json.JSONDecodeError as e:
            self.status_var.set(f"Error decoding JSON: {str(e)}")
            messagebox.showerror("Error", f"Error decoding JSON response:\n{str(e)}")
        except Exception as e:
            self.status_var.set(f"Error processing API data: {str(e)}")
            messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")

    def refresh_all(self):
        self.update_local_info()
        self.fetch_api_data_threaded()


if __name__ == "__main__":
    root = tk.Tk()
    app = DeviceInfoUI(root)
    root.mainloop()
