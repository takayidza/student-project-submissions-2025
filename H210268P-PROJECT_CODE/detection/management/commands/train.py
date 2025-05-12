from django.core.management.base import BaseCommand
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
import joblib

class Command(BaseCommand):
    help = "Train the accident detection model"

    def handle(self, *args, **options):
        # Hardcoded path to the CSV file
        data_path = "accident_data.csv"

        # Load dataset
        self.stdout.write(f"Loading dataset from {data_path}...")
        df = pd.read_csv(data_path)

        # Drop non-numeric features (converting categorical features later if needed)
        df = df.drop(columns=["Latitude", "Longitude", "Road Type", "Road Condition", "Weather", "Lighting", 
                              "Road Curvature", "Elevation & Gradient", "Pedestrian Activity", "Road Signage", 
                              "Guardrails"])

        # Define features (X) and target (y)
        X = df.drop(columns=["Accident Prone"])
        y = df["Accident Prone"]

        # Split into training and testing sets (80% train, 20% test)
        self.stdout.write("Splitting data into training and testing sets...")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        # Initialize and train Random Forest model with verbosity
        self.stdout.write("Initializing and training the Random Forest model...")
        model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced", verbose=2)

        # Train the model
        model.fit(X_train, y_train)

        # Predict on test data
        self.stdout.write("Evaluating the model...")
        y_pred = model.predict(X_test)

        # Evaluate model
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred)

        self.stdout.write(f"Model Accuracy: {accuracy}")
        self.stdout.write("\nClassification Report:\n")
        self.stdout.write(report)

        # Save trained model
        joblib.dump(model, "accident_model.pkl")
        self.stdout.write("Trained model saved as accident_model.pkl")
