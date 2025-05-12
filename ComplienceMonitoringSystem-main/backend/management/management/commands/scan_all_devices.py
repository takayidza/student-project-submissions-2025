import logging
from django.core.management.base import BaseCommand
from management.models import Device  # Adjust this import to match your actual Device model location
from management.utilites.scanner import DeviceScanner  # Adjust this path if needed

logger = logging.getLogger(__name__)
from management.scanners.compliance_scanner import ComplianceScanner


def scan_all_devices():
    scanner = ComplianceScanner()
    devices = Device.objects.all()

    for device in devices:
        is_compliant, violations = scanner.scan_device(device)
        print(f"Device {device.hostname} - Compliant: {is_compliant}")
        if violations:
            print(f"Violations found: {len(violations)}")


# Or scan a single device
def scan_single_device(device_id):
    scanner = ComplianceScanner()
    device = Device.objects.get(id=device_id)
    return scanner.scan_device(device)

class Command(BaseCommand):
    help = 'Scan all devices for policy compliance'

    def handle(self, *args, **kwargs):
        scan_all_devices()
        devices = Device.objects.all()
        total = devices.count()
        logger.info(f"Starting scan for all devices. Total devices: {total}")
        self.stdout.write(f"Scanning {total} devices...")

        for i, device in enumerate(devices, 1):
            try:
                scanner = DeviceScanner(device)
                compliant, violations = scanner.scan_device()
                status = "Compliant" if compliant else f"Non-compliant ({len(violations)} violations)"
                self.stdout.write(f"[{i}/{total}] {device.hostname} - {status}")
            except Exception as e:
                logger.error(f"Failed to scan device {device.hostname}: {str(e)}")
                self.stderr.write(f"[{i}/{total}] {device.hostname} - ERROR: {str(e)}")

        self.stdout.write("All device scans completed.")
