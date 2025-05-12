from django.http import JsonResponse
from django.shortcuts import render
from Dashboard.models import WaterLevel
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pandas as pd
from datetime import timedelta, datetime
import requests

def monitor_water_levels(request):
    return render(request, "Monitoring/MonitorWaterLevels.html")

def predict_hourly_water_usage(request):
    SEQ_LENGTH = 720
    PREDICT_HOURS = 24
    FEATURES = ['water_level', 'temperature', 'humidity']

    # --------------------------
    # Load recent data
    # --------------------------
    water_data = WaterLevel.objects.select_related('sensor_data').order_by('-timestamp')[:SEQ_LENGTH+1]
    if len(water_data) < SEQ_LENGTH + 1:
        return JsonResponse({"error": "Not enough data for prediction."}, status=400)

    water_data = list(reversed(water_data))  # Chronological order

    timestamps = [w.timestamp for w in water_data]
    levels = [w.level for w in water_data]
    temps = [w.sensor_data.temperature for w in water_data]
    hums = [w.sensor_data.humidity for w in water_data]

    df = pd.DataFrame({
        'timestamp': timestamps,
        'water_level': levels,
        'temperature': temps,
        'humidity': hums
    })

    # Save current level for later accumulation
    current_level = df['water_level'].iloc[-1]

    # Normalize inputs
    scaler_x = MinMaxScaler()
    scaled_input = scaler_x.fit_transform(df[FEATURES])
    X_input = scaled_input[:-1].reshape(1, SEQ_LENGTH, len(FEATURES))

    # --------------------------
    # Load model & predict
    # --------------------------
    model = load_model("models/lstm_hourly_water_usage.keras")
    output_shape = model.output_shape[-1]

    predicted_usages = []

    if output_shape == PREDICT_HOURS:
        predicted_usages = model.predict(X_input)[0]
    elif output_shape == 12 and PREDICT_HOURS == 24:
        first_half = model.predict(X_input)[0]
        predicted_usages.extend(first_half)

        for usage in first_half:
            last_temp = df['temperature'].iloc[-1]
            last_humidity = df['humidity'].iloc[-1]
            new_input = np.array([[usage, last_temp, last_humidity]])
            new_scaled = scaler_x.transform(new_input)
            X_input = np.append(X_input[:, 1:, :], new_scaled.reshape(1, 1, 3), axis=1)

        second_half = model.predict(X_input)[0]
        predicted_usages.extend(second_half)
    else:
        return JsonResponse({"error": f"Model output shape {output_shape} not supported."}, status=500)

    # --------------------------
    # Inverse scale & accumulate
    # --------------------------
    df['water_usage'] = df['water_level'].shift(-1) - df['water_level']
    df.dropna(inplace=True)

    scaler_y = MinMaxScaler()
    scaler_y.fit(df[['water_usage']])

    predicted_usages_real = scaler_y.inverse_transform(np.array(predicted_usages).reshape(-1, 1)).flatten()

    predicted_levels = []
    level = current_level
    for usage in predicted_usages_real:
        level += usage
        predicted_levels.append(level)

    future_times = pd.date_range(df['timestamp'].iloc[-1] + pd.Timedelta(hours=1), periods=PREDICT_HOURS, freq='H')

    # Prepare response safely
    result = [
    {
        "timestamp": str(future_times[i].strftime("%H:%M")),
        "predicted_water_usage": round(float(predicted_usages_real[i]), 2),
        "predicted_water_level": round(float(predicted_levels[i]), 2),
    }
    for i in range(PREDICT_HOURS)
]

    return JsonResponse(result, safe=False)

def predict_weekly_usage(request):
    try:
        # Constants
        SEQ_LENGTH = 720
        PREDICT_DAYS = 7
        FEATURES = ['water_level', 'temperature', 'humidity']
        
        # Step 1: Fetch latest data
        water_data = list(
            WaterLevel.objects.select_related('sensor_data')
            .order_by('-timestamp')[:SEQ_LENGTH+1]
        )[::-1]  # Reverse to chronological

        if len(water_data) < SEQ_LENGTH + 1:
            return JsonResponse({'error': 'Not enough data to generate prediction'}, status=400)

        # Step 2: Prepare dataframe
        data = {
            'timestamp': [w.timestamp for w in water_data],
            'water_level': [w.level for w in water_data],
            'temperature': [w.sensor_data.temperature for w in water_data],
            'humidity': [w.sensor_data.humidity for w in water_data],
        }
        df = pd.DataFrame(data)

        # Step 3: Normalize input
        scaler_x = MinMaxScaler()
        scaled_input = scaler_x.fit_transform(df[FEATURES])
        X_input = scaled_input[:-1].reshape(1, SEQ_LENGTH, len(FEATURES))

        # Step 4: Load model
        model = load_model('models/lstm_weekly_water_usage_model.keras')
        output_shape = model.output_shape[-1]
        predicted_usages = model.predict(X_input)[0]

        # Step 5: Inverse scale
        df['water_usage'] = df['water_level'].shift(-1) - df['water_level']
        df.dropna(inplace=True)
        scaler_y = MinMaxScaler()
        scaler_y.fit(df[['water_usage']])
        predicted_usages_real = scaler_y.inverse_transform(
            np.array(predicted_usages).reshape(-1, 1)).flatten()

        # Step 6: Accumulate into water levels
        current_level = df['water_level'].iloc[-1]
        predicted_levels = []
        level = current_level
        for usage in predicted_usages_real:
            level += usage
            predicted_levels.append(round(level, 2))

        # Step 7: Prepare response
        start_time = df['timestamp'].iloc[-1] + timedelta(days=1)
        timestamps = [start_time + timedelta(days=i) for i in range(PREDICT_DAYS)]
        response = [
            {
                'timestamp': ts.strftime('%A'),
                'predicted_water_usage': float(round(usage, 2)),
                'predicted_water_level': float(round(level_val, 2))
            }
            for ts, usage, level_val in zip(timestamps, predicted_usages_real, predicted_levels)
        ]


        return JsonResponse(response, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

def weather_forecast(request):
    API_KEY = "58cce23771e51e527f7caa9db0f15729"  # Add your OpenWeather API key
    lat = -17.8252  # Harare latitude
    lon = 31.0335   # Harare longitude

    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,current,alerts&appid={API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        return JsonResponse({'error': 'Failed to fetch weather data'}, status=500)

    data = response.json()

    hourly_forecast = [
        {
            'timestamp': datetime.fromtimestamp(hour['dt']).strftime('%H%M'),
            'temperature': round(hour['temp'], 2),
            'humidity': hour['humidity']
        }
        for hour in data.get('hourly', [])[:24]
    ]

    daily_forecast = [
        {
            'timestamp': datetime.fromtimestamp(day['dt']).strftime('%a'),
            'temperature_avg': round((day['temp']['min'] + day['temp']['max']) / 2, 2),
            'temperature_min': day['temp']['min'],
            'temperature_max': day['temp']['max'],
            'humidity': day['humidity']
        }
        for day in data.get('daily', [])[:7]
    ]

    return JsonResponse({
        'hourly': hourly_forecast,
        'daily': daily_forecast
    })

