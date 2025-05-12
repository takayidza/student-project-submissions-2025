from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils import timezone

from management.models import ActivityReport



class Command(BaseCommand):
    help = 'Clean up old scan reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Delete reports older than this many days'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options['days'])
        qs = ActivityReport.objects.filter(scan_time__lt=cutoff)

        if options['dry_run']:
            self.stdout.write(
                f"Would delete {qs.count()} reports older than {cutoff}"
            )
        else:
            deleted, _ = qs.delete()
            self.stdout.write(self.style.SUCCESS(
                f"Deleted {deleted} reports older than {cutoff}"
            ))