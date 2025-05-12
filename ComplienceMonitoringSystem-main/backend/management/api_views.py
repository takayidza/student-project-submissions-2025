import logging
import psutil
import platform

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .scanners.compliance_scanner import scan_single_device

from .models import Device
import socket
from datetime import datetime
import os

# Set up logger
logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def device_monitoring(request, device_id):
    try:
        logger.info(f"Fetching device with ID {device_id}")
        device = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        logger.warning(f"Device with ID {device_id} not found")
        return JsonResponse({'error': 'Device not found'}, status=404)

    if request.user.role != 'Admin' and device.user != request.user:
        logger.warning(f"User {request.user.username} denied access to device {device_id}")
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        logger.debug("Fetching system metrics")

        memory = psutil.virtual_memory()
        memory_percent = device.json_data['performance_metrics']['memory']['percent']
        disk_percent = device.json_data['performance_metrics']['disks'][0]['percent']

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'memory': proc.info['memory_percent'],
                    'memory_bytes': proc.info['memory_info'].rss,
                    'status': proc.info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        processes = sorted(processes, key=lambda p: p['cpu'], reverse=True)[:50]
        overall_cpu_usage = device.json_data['performance_metrics']['cpu']['overall_usage']

        alerts = generate_alerts(overall_cpu_usage, memory_percent, disk_percent)

        response_data = {
            'cpu': {
                'usage': round(overall_cpu_usage, 2),
                'cores': device.json_data['performance_metrics']['cpu']['core_count'],
                'model': device.json_data['performance_metrics']['cpu']['model'],
            },
            'memory': {
                'total': device.json_data['performance_metrics']['memory']['total'],
                'used': device.json_data['performance_metrics']['memory']['used'],
                'percent': memory_percent
            },
            'disk': {
                'total': device.json_data['performance_metrics']['disks'][0]['total'],
                'used': device.json_data['performance_metrics']['disks'][0]['used'],
                'percent': disk_percent
            },
            'network': {
                'down': device.json_data['performance_metrics']['network']['bytes_recv'],
                'up': device.json_data['performance_metrics']['network']['bytes_sent']
            },
            'processes': processes,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Successfully gathered metrics for device {device_id}")
        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error in device_monitoring: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def process_details(request, device_id, pid):
    try:
        device = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        logger.warning(f"Device with ID {device_id} not found for process details")
        return JsonResponse({'error': 'Device not found'}, status=404)

    if request.user.role != 'Admin' and device.user != request.user:
        logger.warning(f"User {request.user.username} denied access to process {pid} on device {device_id}")
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        proc = psutil.Process(pid)
        with proc.oneshot():
            process_info = {
                'pid': proc.pid,
                'name': proc.name(),
                'status': proc.status(),
                'cpu': proc.cpu_percent(),
                'memory': proc.memory_percent(),
                'memory_bytes': proc.memory_info().rss,
                'user': proc.username(),
                'command': ' '.join(proc.cmdline()) if proc.cmdline() else proc.exe(),
                'start_time': datetime.fromtimestamp(proc.create_time()).isoformat()
            }

        logger.info(f"Fetched process details for PID {pid}")
        return JsonResponse(process_info)

    except psutil.NoSuchProcess:
        logger.warning(f"Process {pid} not found")
        return JsonResponse({'error': 'Process not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in process_details: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def kill_process(request, device_id, pid):
    try:
        device = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        logger.warning(f"Device with ID {device_id} not found for kill_process")
        return JsonResponse({'error': 'Device not found'}, status=404)

    if request.user.role != 'Admin' and device.user != request.user:
        logger.warning(f"User {request.user.username} denied access to kill process {pid}")
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        proc = psutil.Process(pid)
        proc.terminate()
        logger.info(f"Process {pid} terminated successfully by user {request.user.username}")
        return JsonResponse({'success': True, 'message': f'Process {pid} terminated successfully'})
    except psutil.NoSuchProcess:
        logger.warning(f"Process {pid} not found for termination")
        return JsonResponse({'error': 'Process not found'}, status=404)
    except psutil.AccessDenied:
        logger.warning(f"Access denied while trying to kill process {pid}")
        return JsonResponse({'error': 'Permission denied to kill process'}, status=403)
    except Exception as e:
        logger.error(f"Error in kill_process: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def generate_alerts(cpu_usage, memory_percent, disk_percent):
    alerts = []

    if cpu_usage > 90:
        alerts.append({
            'title': 'High CPU Usage',
            'message': f'CPU usage is at {cpu_usage}%',
            'severity': 'critical',
            'timestamp': datetime.now().isoformat()
        })
    elif cpu_usage > 75:
        alerts.append({
            'title': 'Elevated CPU Usage',
            'message': f'CPU usage is at {cpu_usage}%',
            'severity': 'warning',
            'timestamp': datetime.now().isoformat()
        })

    if memory_percent > 90:
        alerts.append({
            'title': 'High Memory Usage',
            'message': f'Memory usage is at {memory_percent}%',
            'severity': 'critical',
            'timestamp': datetime.now().isoformat()
        })
    elif memory_percent > 75:
        alerts.append({
            'title': 'Elevated Memory Usage',
            'message': f'Memory usage is at {memory_percent}%',
            'severity': 'warning',
            'timestamp': datetime.now().isoformat()
        })

    if disk_percent > 90:
        alerts.append({
            'title': 'Low Disk Space',
            'message': f'Disk usage is at {disk_percent}%',
            'severity': 'critical',
            'timestamp': datetime.now().isoformat()
        })
    elif disk_percent > 80:
        alerts.append({
            'title': 'Disk Space Warning',
            'message': f'Disk usage is at {disk_percent}%',
            'severity': 'warning',
            'timestamp': datetime.now().isoformat()
        })

    return alerts


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Device, InstalledSoftware, BlockedSoftware
import subprocess
import re
import json
from datetime import datetime


@csrf_exempt
@require_http_methods(["GET"])
def device_software_list(request, device_id):
    try:
        device = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)

    # Check permissions
    if request.user.role != 'Admin' and device.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    software_list = InstalledSoftware.objects.filter(device=device).values(
        'id', 'name', 'version', 'publisher', 'install_date', 'status'
    )

    return JsonResponse(list(software_list), safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def scan_device_software(request, device_id):
    try:
        device = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)

    # Check permissions
    if request.user.role != 'Admin' and device.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        # Get installed software based on OS
        installed_software = get_installed_software(device.os)

        # Save to database
        saved_software = []
        for software in installed_software:
            sw, created = InstalledSoftware.objects.update_or_create(
                device=device,
                name=software['name'],
                defaults={
                    'version': software.get('version', 'Unknown'),
                    'publisher': software.get('publisher', 'Unknown'),
                    'install_date': software.get('install_date', datetime.now()),
                    'status': 'pending'  # Will be updated in compliance check
                }
            )
            saved_software.append({
                'id': sw.id,
                'name': sw.name,
                'version': sw.version,
                'publisher': sw.publisher
            })

        # Check against blocked software
        compliance_results = check_software_compliance(device.id)

        return JsonResponse({
            'success': True,
            'scanned_count': len(saved_software),
            'blocked_count': compliance_results['blocked_count'],
            'software': saved_software,
            'compliance_status': compliance_results['status']
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def software_detail(request, device_id, software_id):
    try:
        device = Device.objects.get(pk=device_id)
        software = InstalledSoftware.objects.get(pk=software_id, device=device)
    except Device.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)
    except InstalledSoftware.DoesNotExist:
        return JsonResponse({'error': 'Software not found'}, status=404)

    # Check permissions
    if request.user.role != 'Admin' and device.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    software_data = {
        'id': software.id,
        'name': software.name,
        'version': software.version,
        'publisher': software.publisher,
        'install_date': software.install_date,
        'status': software.status,
        'device': {
            'id': device.id,
            'hostname': device.hostname,
            'os': device.os
        }
    }

    return JsonResponse(software_data)


@csrf_exempt
@require_http_methods(["GET"])
def check_software_compliance(request, device_id, software_id):
    try:
        device = Device.objects.get(pk=device_id)
        software = InstalledSoftware.objects.get(pk=software_id, device=device)
    except Device.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)
    except InstalledSoftware.DoesNotExist:
        return JsonResponse({'error': 'Software not found'}, status=404)

    # Check permissions
    if request.user.role != 'Admin' and device.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    # Check against blocked software
    blocked_software = BlockedSoftware.objects.filter(
        Q(applicable_os=device.os) | Q(applicable_os='all'),
        active=True
    )

    is_blocked = False
    matched_block = None

    for blocked in blocked_software:
        if blocked.detection_pattern:
            if re.search(blocked.detection_pattern, software.name, re.IGNORECASE):
                is_blocked = True
                matched_block = blocked
                break
        else:
            if blocked.name.lower() in software.name.lower():
                is_blocked = True
                matched_block = blocked
                break

    if is_blocked:
        software.status = 'blocked'
        software.save()

        return JsonResponse({
            'is_compliant': False,
            'status': 'blocked',
            'severity': matched_block.severity,
            'blocked_software': {
                'id': matched_block.id,
                'name': matched_block.name,
                'description': matched_block.description
            },
            'message': f'Software matches blocked entry: {matched_block.name}'
        })
    else:
        software.status = 'approved'
        software.save()

        return JsonResponse({
            'is_compliant': True,
            'status': 'approved',
            'message': 'Software is compliant with policies'
        })


@csrf_exempt
@require_http_methods(["GET"])
def check_blocked_software(request, device_id):
    try:
        device = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)

    # Check permissions
    if request.user.role != 'Admin' and device.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    # Get all installed software for device
    installed_software = InstalledSoftware.objects.filter(device=device)

    # Get applicable blocked software
    blocked_software = BlockedSoftware.objects.filter(
        Q(applicable_os=device.os) | Q(applicable_os='all'),
        active=True
    )

    # Check for matches
    blocked_matches = []
    for software in installed_software:
        for blocked in blocked_software:
            if blocked.detection_pattern:
                if re.search(blocked.detection_pattern, software.name, re.IGNORECASE):
                    blocked_matches.append({
                        'installed_software': {
                            'id': software.id,
                            'name': software.name,
                            'version': software.version
                        },
                        'blocked_software': {
                            'id': blocked.id,
                            'name': blocked.name,
                            'severity': blocked.severity,
                            'description': blocked.description
                        }
                    })
                    break
            else:
                if blocked.name.lower() in software.name.lower():
                    blocked_matches.append({
                        'installed_software': {
                            'id': software.id,
                            'name': software.name,
                            'version': software.version
                        },
                        'blocked_software': {
                            'id': blocked.id,
                            'name': blocked.name,
                            'severity': blocked.severity,
                            'description': blocked.description
                        }
                    })
                    break

    return JsonResponse({
        'device_id': device.id,
        'hostname': device.hostname,
        'os': device.os,
        'total_installed': installed_software.count(),
        'blocked_count': len(blocked_matches),
        'matches': blocked_matches
    })


# Helper function to get installed software (platform-specific)
def get_installed_software(os_type):
    software_list = []

    try:
        if os_type.lower() == 'windows':
            # PowerShell command to get installed software
            cmd = 'powershell "Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate | ConvertTo-Json"'
            output = subprocess.check_output(cmd, shell=True)
            software_data = json.loads(output)

            for item in software_data:
                if item['DisplayName']:
                    software_list.append({
                        'name': item['DisplayName'],
                        'version': item['DisplayVersion'] if 'DisplayVersion' in item else 'Unknown',
                        'publisher': item['Publisher'] if 'Publisher' in item else 'Unknown',
                        'install_date': parse_windows_date(item['InstallDate']) if 'InstallDate' in item else None
                    })

        elif os_type.lower() == 'linux':
            # Check for dpkg (Debian/Ubuntu)
            try:
                output = subprocess.check_output(['dpkg', '-l'], universal_newlines=True)
                for line in output.split('\n')[5:]:
                    if line:
                        parts = re.split(r'\s+', line.strip())
                        if len(parts) >= 3:
                            software_list.append({
                                'name': parts[1],
                                'version': parts[2],
                                'publisher': 'Unknown',
                                'install_date': None
                            })
            except:
                pass

            # Check for rpm (RedHat/CentOS)
            try:
                output = subprocess.check_output(['rpm', '-qa', '--queryformat', '%{NAME}\t%{VERSION}\t%{VENDOR}\n'],
                                                 universal_newlines=True)
                for line in output.split('\n'):
                    if line:
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            software_list.append({
                                'name': parts[0],
                                'version': parts[1],
                                'publisher': parts[2] if len(parts) > 2 else 'Unknown',
                                'install_date': None
                            })
            except:
                pass

        elif os_type.lower() == 'macos':
            # System Profiler command for macOS
            cmd = 'system_profiler SPApplicationsDataType -json'
            output = subprocess.check_output(cmd, shell=True)
            software_data = json.loads(output)

            for app in software_data.get('SPApplicationsDataType', []):
                software_list.append({
                    'name': app.get('_name', 'Unknown'),
                    'version': app.get('version', 'Unknown'),
                    'publisher': app.get('obtained_from', 'Unknown'),
                    'install_date': None
                })

    except Exception as e:
        print(f"Error getting installed software: {str(e)}")

    return software_list


def parse_windows_date(date_str):
    if not date_str:
        return None
    try:
        # Windows install date is often YYYYMMDD
        return datetime.strptime(date_str, '%Y%m%d').date()
    except:
        return None


from django.http import HttpResponse
import os
from django.conf import settings

def download_client_exe(request):
    """
    This view allows users to download the client.exe file.  It's crucial
    to ensure the file's location is secure and that only authorized
    files are served.  This example assumes the file is within your
    project's 'static' directory or a dedicated 'downloads' directory.

    Args:
        request: The Django request object.

    Returns:
        HttpResponse: A streaming HTTP response with the file.  If the
                      file is not found, it returns a 404 error.
    """
    # 1.  Sanitize and Construct the File Path:
    #     -   DO NOT directly use user-provided input (e.g., from request.GET)
    #         to construct the file path.  This is a major security risk
    #         (path traversal vulnerability).
    #     -   Instead, define a safe, controlled location for your downloadable
    #         files, and construct the path programmatically.
    #     -   Use os.path.join to ensure correct path handling across
    #         different operating systems.

    # Example:  Assume 'client.exe' is in a 'downloads' subdirectory
    #          within your project's base directory.
    file_path = os.path.join(settings.BASE_DIR, 'downloads', 'client.exe')

    # 2.  Check if the File Exists:
    #     -   Always verify that the file exists before attempting to open
    #         and serve it.  This prevents errors and potential security
    #         issues.
    if not os.path.exists(file_path):
        #  Consider logging this event for security monitoring.
        #  Example (requires import logging):
        #  logging.error(f"Download attempt for non-existent file: {file_path}")
        return HttpResponse("File not found.", status=404)

    # 3.  Determine the Content Type:
    #     -   Set the correct MIME type for the file.  'application/octet-stream'
    #         is a generic type for binary files, which will force a download
    #         in most browsers.  You can be more specific if you know the
    #         exact type (e.g., 'application/vnd.microsoft.portable-executable'
    #         for .exe files, though this is less universally recognized).
    #     -   For executables, 'application/octet-stream' is generally safest.
    content_type = 'application/octet-stream'

    # 4.  Set the Response Headers:
    #     -   'Content-Disposition':  This header tells the browser how to
    #         handle the file.  'attachment' means it should be downloaded,
    #         and 'filename=client.exe' suggests a name for the downloaded
    #         file.  You can customize the filename if needed.
    #     -  'Content-Length':  While not strictly required, setting the
    #         content length can help the browser display a progress bar
    #         and improve the user experience, especially for large files.
    #     -  'X-Sendfile':  For production, *strongly* consider using
    #        a web server like Nginx or Apache to serve the file
    #        (using X-Sendfile or X-Accel-Redirect). This is *much*
    #        more efficient than having Django read and stream the
    #        file itself.  See the notes below.

    # 5.  Serve the File:
    #     -   Use a 'with open(...)' block to ensure the file is properly
    #         closed, even if errors occur.
    #     -   Use 'rb' mode for reading binary files.
    try:
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="client.exe"'
        response['Content-Length'] = os.path.getsize(file_path)
        return response
    except Exception as e:
        # Handle file reading errors (e.g., disk error, permissions).
        #  Log the error!
        #  logging.error(f"Error reading file for download: {e}")
        return HttpResponse(f"Error: {e}", status=500)

