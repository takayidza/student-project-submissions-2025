import pandas as pd
from django.core.management.base import BaseCommand

from detection.models import AccidentProneArea

import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Import all accident areas from CSV including risk level and whether prone or not.'

    def handle(self, *args, **kwargs):
        file_path = 'accident_data.csv'  # Update path if needed
        df = pd.read_csv(file_path)

        def determine_risk_level(frequency, severity):
            # Customize logic if needed
            if frequency > 50 or severity in ['High', 'Severe']:
                return 'High'
            elif frequency > 20:
                return 'Medium'
            return 'Low'

        imported_count = 0

        for _, row in df.iterrows():
            risk_level = determine_risk_level(
                row['Accident Frequency'],
                row['Accident Severity']
            )

            AccidentProneArea.objects.update_or_create(
                latitude=row['Latitude'],
                longitude=row['Longitude'],
                defaults={
                    'risk_level': risk_level,
                    'accident_prone': bool(int(row['Accident Prone'])),
                    'description': f"{row['Road Type']} - {row['Road Condition']}, {row['Weather']}, {row['Lighting']}",
                }
            )
            imported_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Imported {imported_count} accident area records."))
