
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from management.models import Device
 # Adjust import to match your project

from management.utilites.scanner import DeviceScanner

@shared_task
def scan_devices():
    # Option 1: All devices
    devices = Device.objects.all()

    # Option 2: Filter devices by scan age or missing scan
    # devices = Device.objects.filter(
    #     Q(last_scan__lt=timezone.now() - timedelta(hours=24)) |
    #     Q(last_scan__isnull=True)
    # )

    for device in devices:
        scanner = DeviceScanner(device)
        is_compliant, violations = scanner.scan_device()

        # Example: update device status and last scan time
        device.is_compliant = is_compliant
        device.last_scan = timezone.now()
        device.save()

        # Optionally log or save violations
        if violations:
            print(f'Device {device.id} violations: {violations}')
