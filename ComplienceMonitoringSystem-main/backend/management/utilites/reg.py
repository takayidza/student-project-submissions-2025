import json
from django.utils import timezone
from datetime import datetime



def create_or_update_device(json_data, user):
    from management.models import Device, InstalledSoftware, User
    # Parse the JSON data
    data = json.loads(json_data) if isinstance(json_data, str) else json_data
    memory_percent = data['performance_metrics']['memory']['percent']
    disk_percent = data['performance_metrics']['disks'][0]['percent']
    # Get or create the device
    device, created = Device.objects.get_or_create(
        hostname=data['hostname'],
        defaults={
            # 'user': user,
            'department': 'Unknown',  # Default department since not in JSON
            'ip_address': data['ip_address'],
            'os': data['os_info']['system'],
            'device_type': 'laptop',  # Default type since not in JSON
            'actions': 'Initial scan',  # Default actions
            'status': 'non-compliant'  # Default status
        }
    )
    device.json_data = data
    overall_cpu_usage = data['performance_metrics']['cpu']['overall_usage']

    # Update device fields if it already existed
    if not created:
        device.ip_address = data['ip_address']
        device.os = data['os_info']['system']
        device.cpu_usage= round(overall_cpu_usage, 2)
        device.disk_usage = disk_percent
        device.memory_usage = memory_percent
        device.last_scan = timezone.now()
        device.network_upload_speed = data['performance_metrics']['network']['bytes_sent']
        device.network_download_speed  = data['performance_metrics']['network']['bytes_recv']
        device.save()
    if created:
        device.user = user
        device.save()
    # Process installed software
    if 'installed_software' in data:
        # First get all current software for this device
        current_software = list(device.installedsoftware.all())

        # Process each software in the JSON
        for software_data in data['installed_software']:
            # Skip if no name is provided
            if 'name' not in software_data or not software_data['name']:
                continue

            # Parse install date if available
            install_date = None
            if 'install_date' in software_data:
                try:
                    install_date = datetime.strptime(software_data['install_date'], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass

            # Get or create the software
            software, s_created = InstalledSoftware.objects.get_or_create(
                device=device,
                name=software_data['name'],
                defaults={
                    'version': software_data.get('version', ''),
                    'publisher': software_data.get('publisher', ''),
                }
            )

            # Update if it already existed
            if not s_created:
                software.version = software_data.get('version', software.version)
                software.publisher = software_data.get('publisher', software.publisher)
                software.save()

            # Remove from current_software list if found
            for cs in current_software[:]:
                if cs.name == software.name:
                    current_software.remove(cs)
                    break

        # Any remaining in current_software are no longer installed - delete them
        for obsolete_software in current_software:
            obsolete_software.delete()

    return device

# Example usage:
# Assuming you have a User instance and the JSON data
# user = User.objects.get(username='someuser')
# device = create_or_update_device(json_data, user)