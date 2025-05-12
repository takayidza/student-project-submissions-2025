from django.core.management.base import BaseCommand
from pathlib import Path
import shutil
from django.conf import settings
import datetime


class Command(BaseCommand):
    help = 'Backup compliance data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--destination',
            type=str,
            default='./backups',
            help='Backup destination directory'
        )

    def handle(self, *args, **options):
        dest = Path(options['destination'])
        dest.mkdir(exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        files = [
            ('management/ml/data/training_data.csv', f'training_data_{timestamp}.csv'),
            ('management/ml/models/compliance_model.joblib', f'model_{timestamp}.joblib'),
        ]

        for src, filename in files:
            src_path = Path(settings.BASE_DIR) / src
            if src_path.exists():
                shutil.copy2(src_path, dest / filename)
                self.stdout.write(f"Backed up {src} to {dest / filename}")
            else:
                self.stdout.write(self.style.WARNING(f"Source file not found: {src}"))