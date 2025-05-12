# Updated train_accident_model.py with verbosity to show training details

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
import joblib

def train_accident_model(data_path="accident_data.csv"):
    # Load dataset
    df = pd.read_csv("data_path")

    # Drop non-numeric features (converting categorical features later if needed)
    df = df.drop(columns=["Latitude", "Longitude", "Road Type", "Road Condition", "Weather", "Lighting", 
                          "Road Curvature", "Elevation & Gradient", "Pedestrian Activity", "Road Signage", 
                          "Guardrails"])

    # Define features (X) and target (y)
    X = df.drop(columns=["Accident Prone"])
    y = df["Accident Prone"]

    # Split into training and testing sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Initialize and train Random Forest model with verbosity
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced", verbose=2)

    # Train the model
    model.fit(X_train, y_train)

    # Predict on test data
    y_pred = model.predict(X_test)

    # Evaluate model
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    print("Model Accuracy:", accuracy)
    print("\nClassification Report:\n", report)

    # Save trained model
    joblib.dump(model, "accident_model.pkl")
    print("Trained model saved as accident_model.pkl")

# Train the model with increased verbosity
train_accident_model()
