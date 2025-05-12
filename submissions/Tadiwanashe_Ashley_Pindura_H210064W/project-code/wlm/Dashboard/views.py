from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import WaterLevel
from django.shortcuts import render
import pandas as pd
from django.utils.timezone import now, timedelta
from datetime import datetime
import csv
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import SensorData, WaterLevel  # Make sure you import your models!
from django.utils.timezone import make_aware
import pytz
from django.utils import timezone


latest_data = {
    "water_level": None,
    "temperature": None,
    "humidity": None,
    "timestamp": None
}

@csrf_exempt
def send_data(request):
    global latest_data  # 🛡️ Tell Python we are using the global variable

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            water_level = data.get("water_level")
            temperature = data.get("temperature")
            humidity = data.get("humidity")

            if water_level is None or temperature is None or humidity is None:
                return JsonResponse({"error": "Missing data fields"}, status=400)

            print({
                "water_level": water_level,
                "temperature": temperature,
                "humidity": humidity
            })

            # Save to database
            sensor = SensorData.objects.create(
                temperature=temperature,
                humidity=humidity
            )
            WaterLevel.objects.create(
                level=water_level,
                sensor_data=sensor
            )

            # 🔥 Update the global latest_data
            latest_data = {
                "water_level": water_level,
                "temperature": temperature,
                "humidity": humidity,
                "timestamp": sensor.timestamp
            }

            return JsonResponse({
                "message": "Data received successfully!",
                **latest_data
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def get_latest_water_level(request):
    # ⚡ Use in-memory latest_data instead of database
    if latest_data["water_level"] is not None:
        return JsonResponse({
            "water_level": latest_data["water_level"],
            "temperature": latest_data["temperature"],
            "humidity": latest_data["humidity"],
            "timestamp": latest_data["timestamp"]
        })
    return JsonResponse({"error": "No data available yet"})

def Get_Hourly_Data(request):
    # Set the target start and end time for April 30, 2025
    start_time = datetime(2025, 4, 30, 0, 0)  # Starting at 00:00
    end_time = datetime(2025, 4, 30, 23, 59)  # Ending at 23:59 (end of the day)

    # Query water level data in the time window
    water_levels = WaterLevel.objects.filter(
        timestamp__gte=start_time,
        timestamp__lte=end_time
    ).exclude(level=0).values('timestamp', 'level')

    df = pd.DataFrame.from_records(water_levels)

    if df.empty:
        return JsonResponse({"error": "No data available"}, status=404)

    # Convert timestamp column to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Resample in 4-hour intervals using the average (or you can use .max() or .min())
    df.set_index('timestamp', inplace=True)
    df_resampled = df.resample('4H').mean().dropna().reset_index()

    # Format time as HH:MM
    df_resampled['timestamp'] = df_resampled['timestamp'].dt.strftime('%H:%M')

    # Prepare JSON response
    chart_data = df_resampled.to_dict(orient='records')
    return JsonResponse({"chart_data": chart_data})

def dashboard(request):
    return render(request, 'Dashboard/dashboard.html')

def Get_last24_Water_Usage(request):
    # Set the target date (April 29, 2025)
    start_time = datetime(2025, 4, 29, 0, 0)
    end_time = start_time + timedelta(days=1)

    # Query water level data for the day
    water_levels = WaterLevel.objects.filter(
        timestamp__gte=start_time,
        timestamp__lt=end_time
    ).exclude(level=0).values('timestamp', 'level')

    # Convert to DataFrame
    df = pd.DataFrame.from_records(water_levels)

    if df.empty:
        return JsonResponse({"error": "No data available"}, status=404)

    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Calculate water usage
    df['water_usage'] = df['level'].diff().fillna(0)

    # Resample hourly
    df.set_index('timestamp', inplace=True)
    df_resampled = df.resample('H').mean().dropna().reset_index()

    # Format timestamp and round values
    df_resampled['timestamp'] = df_resampled['timestamp'].dt.strftime('%H%M')
    df_resampled['level'] = df_resampled['level'].round(2)
    df_resampled['water_usage'] = df_resampled['water_usage'].round(2)

    # Prepare response
    chart_data = df_resampled[['timestamp', 'level', 'water_usage']].to_dict(orient='records')
    return JsonResponse({"chart_data": chart_data})


