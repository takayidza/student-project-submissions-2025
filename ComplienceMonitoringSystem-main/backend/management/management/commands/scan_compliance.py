from django.core.management.base import BaseCommand, CommandError
from management.scanners.compliance_scanner import scan_all_devices, scan_single_device
from management.models import Device

class Command(BaseCommand):
    help = 'Run compliance scan on all devices or a single device'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device',
            type=int,
            help='ID of a single device to scan. If omitted, all devices will be scanned.',
        )

    def handle(self, *args, **options):
        device_id = options.get('device')

        if device_id:
            try:
                device = Device.objects.get(id=device_id)
                is_compliant, violations = scan_single_device(device_id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Scanned device {device.hostname} - Compliant: {is_compliant}"
                    )
                )
                if violations:
                    self.stdout.write(f"Violations found: {len(violations)}")
            except Device.DoesNotExist:
                raise CommandError(f"Device with ID {device_id} does not exist.")
        else:
            scan_all_devices()
            self.stdout.write(self.style.SUCCESS("Compliance scan completed for all devices."))
