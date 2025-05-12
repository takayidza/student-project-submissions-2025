import time
import requests
from django.core.management.base import BaseCommand
from detection.models import AccidentProneArea, SafetyNotification

class Command(BaseCommand):
    help = 'Create daily safety notifications for accident-prone areas with real place names.'

    def handle(self, *args, **options):
        accident_areas = AccidentProneArea.objects.filter(accident_prone=True)

        created_count = 0

        for area in accident_areas:
            location_name = self.reverse_geocode(area.latitude, area.longitude)

            message = (
                f"⚠️ Accident-prone area detected near {location_name}. "
                f"Please drive safely and be cautious. "
            )

            SafetyNotification.objects.create(
                message=message
            )

            # created_count += 1
            # time.sleep(1)  # Respect Nominatim's rate limit (1 request per second)

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} safety notifications."))

    def reverse_geocode(self, latitude, longitude):
        """Use OpenStreetMap Nominatim to get the address for given coordinates."""
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
        }
        headers = {
            'User-Agent': 'accident-detection-app'  # IMPORTANT: always send a user-agent
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                address = data.get('display_name')
                if address:
                    return address
        except requests.RequestException as e:
            self.stdout.write(self.style.WARNING(f"Reverse geocoding failed: {e}"))

        # Fallback if address not found
        return f"Latitude {latitude}, Longitude {longitude}"
