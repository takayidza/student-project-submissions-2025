from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils import timezone
from management.models import Device, ActivityReport
import csv


class Command(BaseCommand):
    help = 'Generate compliance reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Reporting period in days'
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Export to CSV file'
        )

    def handle(self, *args, **options):
        since = timezone.now() - timedelta(days=options['days'])

        # Device compliance stats
        total = Device.objects.count()
        compliant = Device.objects.filter(status='compliant').count()

        # Recent violations
        violations = ActivityReport.objects.filter(
            scan_status='non-compliant',
            scan_time__gte=since
        ).count()

        # Output report
        report = [
            f"Compliance Report ({options['days']} days)",
            f"Devices: {total} total, {compliant} compliant ({compliant / total:.1%})",
            f"Violations detected: {violations}",
            "Top issues:"
        ]

        # Add top issues
        from django.db.models import Count
        top_issues = ActivityReport.objects.filter(
            scan_status='non-compliant',
            scan_time__gte=since
        ).values('scan_report').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        for issue in top_issues:
            report.append(f"- {issue['count']} devices: {issue['scan_report'][:100]}...")

        # Output or export
        if options['export']:
            with open(options['export'], 'w') as f:
                writer = csv.writer(f)
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Total Devices', total])
                writer.writerow(['Compliant Devices', compliant])
                writer.writerow(['Compliance Rate', f"{compliant / total:.1%}"])
                writer.writerow(['Violations', violations])
            self.stdout.write(self.style.SUCCESS(
                f"Report exported to {options['export']}"
            ))
        else:
            self.stdout.write("\n".join(report))