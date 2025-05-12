from django.core.management.base import BaseCommand
from management.ml.compliance_scanner import scan_all_devices, scan_single_device

from management.models import Device


class Command(BaseCommand):
    help = 'Scan devices for compliance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=int,
            help='Scan a specific device by ID'
        )
        parser.add_argument(
            '--high-risk-only',
            action='store_true',
            help='Scan only high-risk devices'
        )

    def handle(self, *args, **options):
        if options['device_id']:
            compliant, violations = scan_single_device(options['device_id'])
            self.stdout.write(
                f"Device {options['device_id']} - Compliant: {compliant}, "
                f"Violations: {len(violations)}"
            )
        elif options['high_risk_only']:
            from django.db.models import Q
            from datetime import timedelta
            from django.utils import timezone
            Device

            devices = Device.objects.filter(
                Q(last_scan__isnull=True) |
                Q(last_scan__lt=timezone.now() - timedelta(days=30)) |
                Q(installedsoftware__status='blocked')
            ).distinct()[:500]

            for device in devices:
                compliant, violations = scan_single_device(device.id)
                status = self.style.SUCCESS if compliant else self.style.ERROR
                self.stdout.write(status(
                    f"{device.hostname}: {len(violations)} violations"
                ))
        else:
            results = scan_all_devices()
            compliant = sum(1 for r in results if r.get('compliant', False))
            self.stdout.write(
                f"Scanned {len(results)} devices - "
                f"Compliance rate: {compliant / len(results):.1%}"
            )