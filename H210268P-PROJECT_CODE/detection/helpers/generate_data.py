import pandas as pd
import numpy as np
import random

def generate_accident_data(num_records=20000):
    np.random.seed(42)
    random.seed(42)
    
    data = []
    
    for _ in range(num_records):
        latitude = round(np.random.uniform(-18.5, -16.5), 6)
        longitude = round(np.random.uniform(30.5, 32.5), 6)
        accident_frequency = np.random.poisson(10)  # More realistic accident count
        accident_severity = np.random.randint(1, 6)  # Scale of 1-5
        road_type = np.random.choice(["Highway", "Urban Road", "Rural Road"], p=[0.3, 0.5, 0.2])
        road_condition = np.random.choice(["Good", "Fair", "Poor"], p=[0.4, 0.4, 0.2])
        weather = np.random.choice(["Clear", "Rainy", "Foggy"], p=[0.6, 0.3, 0.1])
        lighting = np.random.choice(["Day", "Night"], p=[0.7, 0.3])
        speed_limit = np.random.choice([50, 60, 70, 80, 90, 100, 110, 120])
        traffic_volume = np.random.randint(2000, 30000)
        road_curvature = np.random.choice(["Straight", "Gentle", "Moderate", "Sharp"], p=[0.5, 0.2, 0.2, 0.1])
        elevation_gradient = np.random.choice(["Low", "Medium", "High"], p=[0.5, 0.3, 0.2])
        intersections = np.random.randint(0, 6)
        pedestrian_activity = np.random.choice(["Low", "Medium", "High"], p=[0.6, 0.3, 0.1])
        road_signage = np.random.choice(["Present", "Absent"], p=[0.8, 0.2])
        guardrails = np.random.choice(["Present", "Absent"], p=[0.7, 0.3])
        
        # Determine accident-prone status (1 = Yes, 0 = No) based on risky factors
        accident_prone = 0
        if (
            (accident_frequency > 12) or 
            (accident_severity >= 4) or 
            (road_condition == "Poor" and road_curvature in ["Moderate", "Sharp"]) or 
            (elevation_gradient == "High" and speed_limit >= 90) or 
            (weather in ["Rainy", "Foggy"] and lighting == "Night")
        ):
            accident_prone = 1
        
        data.append([
            latitude, longitude, accident_frequency, accident_severity, road_type, road_condition, 
            weather, lighting, speed_limit, traffic_volume, road_curvature, elevation_gradient, 
            intersections, pedestrian_activity, road_signage, guardrails, accident_prone
        ])
    
    df = pd.DataFrame(data, columns=[
        "Latitude", "Longitude", "Accident Frequency", "Accident Severity", "Road Type", "Road Condition", 
        "Weather", "Lighting", "Speed Limit (km/h)", "Traffic Volume (vehicles/day)", "Road Curvature", 
        "Elevation & Gradient", "Intersections", "Pedestrian Activity", "Road Signage", "Guardrails", "Accident Prone"
    ])
    
    # Remove duplicate locations
    df.drop_duplicates(subset=["Latitude", "Longitude"], keep='first', inplace=True)
    
    # Save dataset
    df.to_csv("accident_data.csv", index=False)
    print("Dataset saved as accident_data.csv with", len(df), "records.")

# Generate dataset
generate_accident_data(20000)
