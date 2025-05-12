import requests
from django.core.management.base import BaseCommand
from detection.models import AccidentProneArea

class Command(BaseCommand):
    help = 'Snap accident-prone area coordinates to nearest road using OSRM'

    def handle(self, *args, **kwargs):
        accident_areas = AccidentProneArea.objects.filter(accident_prone=True)
        updated_count = 0

        for area in accident_areas:
            lon = float(area.longitude)
            lat = float(area.latitude)

            url = f"http://router.project-osrm.org/nearest/v1/driving/{lon},{lat}"
            try:
                response = requests.get(url)
                data = response.json()

                if data.get('code') == 'Ok' and data.get('waypoints'):
                    nearest = data['waypoints'][0]['location']
                    area.longitude = nearest[0]
                    area.latitude = nearest[1]
                    area.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated area {area.id}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Could not find road for {area.id}"))

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error with area {area.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} accident-prone locations."))
