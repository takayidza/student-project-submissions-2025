import os
import pickle
import numpy as np
from sklearn.linear_model import LinearRegression
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)

# Ensure models directory exists
models_dir = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(models_dir, exist_ok=True)

def create_simple_conversion_model():
    """
    Create a simple model that converts pixel speeds (pixels/second) to km/h,
    calibrated using a known real-world distance in the scene.
    """
    logging.info("Creating new conversion factor model...")

    # Calibration: set this to your measured value!
    pixels_per_meter = 34.3  # <-- Replace with your actual calibration

    # Generate synthetic training data (pixels/second)
    pixel_speeds = np.array([50, 100, 200, 300, 400, 500, 600, 700, 800, 900]).reshape(-1, 1)
    # Calculate corresponding km/h
    kmh_speeds = (pixel_speeds / pixels_per_meter) * 3.6

    # Create and train the model
    model = LinearRegression()
    model.fit(pixel_speeds, kmh_speeds)

    # Verify the model
    test_speed = np.array([[300]])  # 300 pixels/second
    predicted_kmh = model.predict(test_speed)[0]
    logging.info(f"Model test: {float(test_speed[0][0])} pixels/sec → {float(predicted_kmh):.2f} km/h")

    # Save the model
    model_path = os.path.join(models_dir, "conversion_factor_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    logging.info(f"Conversion model saved to {model_path}")
    return model_path

if __name__ == "__main__":
    model_path = create_simple_conversion_model()
    print(f"\nModel created successfully at:\n{os.path.abspath(model_path)}")
    print("\nYou can now run the main application.")