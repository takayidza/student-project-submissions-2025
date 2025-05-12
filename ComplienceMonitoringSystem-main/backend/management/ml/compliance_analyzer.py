import joblib
import pandas as pd
from django.utils import timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from pathlib import Path
import os
import pytz
from datetime import datetime
import numpy as np
from django.db import transaction

MODEL_PATH = Path(__file__).parent / 'models' / 'compliance_model.joblib'
TRAINING_DATA_PATH = Path(__file__).parent / 'data' / 'training_data.csv'


class ComplianceAnalyzer:
    def __init__(self):
        self.model = None
        self.features = [
            'os_type', 'device_type', 'days_since_last_scan',
            'num_installed_software', 'num_blocked_software',
            'pct_compliant_history'
        ]
        self.load_model()
        self.ensure_training_data_file()

    def ensure_training_data_file(self):
        """Ensure training data file exists with header"""
        if not os.path.exists(TRAINING_DATA_PATH):
            os.makedirs(TRAINING_DATA_PATH.parent, exist_ok=True)
            with open(TRAINING_DATA_PATH, 'w') as f:
                f.write(','.join(self.features + ['label']) + '\n')

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        else:
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced',
                max_depth=10,
                min_samples_leaf=2
            )
            self._initialize_default_model()

    def _initialize_default_model(self):
        """Create a simple default model if no trained model exists"""
        X = np.array([
            # os, device, days, software, blocked, pct_compliant
            [1, 1, 7, 10, 0, 0.9],  # Compliant Windows laptop
            [1, 2, 30, 15, 2, 0.4],  # Non-compliant Windows desktop
            [2, 1, 14, 8, 0, 0.6],  # Warning Mac laptop
            [3, 4, 60, 20, 3, 0.2],  # Non-compliant Linux server
            [1, 1, 3, 12, 0, 0.8],  # Compliant Windows laptop
            [2, 2, 21, 10, 1, 0.5]  # Warning Mac desktop
        ])
        y = np.array([2, 0, 1, 0, 2, 1])  # 0: non-compliant, 1: warning, 2: compliant
        self.model.fit(X, y)
        self.save_model()

    def save_model(self):
        os.makedirs(MODEL_PATH.parent, exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)

    def preprocess_data(self, device_data, software_list):
        """Convert raw data into features for the model"""
        # OS type encoding
        os_mapping = {
            'windows': 1, 'mac': 2, 'linux': 3, 'ubuntu': 3, 'debian': 3,
            'fedora': 3, 'red hat': 3, 'centos': 3, 'suse': 3, 'arch': 3,
            'kali': 3, 'freebsd': 4, 'openbsd': 4, 'ios': 5, 'ipados': 5,
            'android': 6, 'chrome': 7, 'solaris': 8, 'aix': 8, 'hp-ux': 8
        }
        os_type = next(
            (v for k, v in os_mapping.items() if k in device_data['os'].lower()),
            3  # Default to Linux
        )

        # Device type encoding
        device_type = {
            'laptop': 1,
            'desktop': 2,
            'mobile': 3,
            'server': 4,
            'tablet': 5,
            'vm': 6,
            'container': 7
        }.get(device_data['device_type'].lower(), 4)  # Default to server

        # Handle datetime comparison
        last_scan = device_data['last_scan']
        if timezone.is_naive(last_scan):
            last_scan = timezone.make_aware(last_scan, timezone=pytz.UTC)

        now = timezone.now()
        if timezone.is_naive(now):
            now = timezone.make_aware(now, timezone=pytz.UTC)

        days_since = (now - last_scan).days

        # Count installed software
        num_software = len(software_list)

        # Count blocked software
        blocked_keywords = ['crack', 'hack', 'keygen', 'patch', 'torrent']
        num_blocked = sum(
            1 for s in software_list
            if any(kw in s['name'].lower() for kw in blocked_keywords) or
            any(kw in s.get('publisher', '').lower() for kw in blocked_keywords)
        )

        # Historical compliance
        history = device_data.get('historical_reports', [])
        if history:
            pct_compliant = sum(
                1 for r in history
                if r.get('scan_status') == 'compliant' or
                r.get('compliance_status') == 'compliant'
            ) / len(history)
        else:
            pct_compliant = 0

        return [
            os_type, device_type, days_since,
            num_software, num_blocked, pct_compliant
        ]

    def predict_compliance_status(self, device_data, software_list):
        try:
            features = self.preprocess_data(device_data, software_list)

            if len(features) != len(self.features):
                raise ValueError(f"Expected {len(self.features)} features, got {len(features)}")

            # Get prediction probabilities
            proba = self.model.predict_proba([features])[0]
            pred_class = self.model.predict([features])[0]

            status_map = {
                0: 'non-compliant',
                1: 'warning',
                2: 'compliant'
            }

            return {
                'status': status_map.get(pred_class, 'non-compliant'),
                'confidence': float(max(proba)),
                'recommended_actions': self.get_recommendations(pred_class, software_list),
                'explanation': self.generate_explanation(features, pred_class),
                'features': dict(zip(self.features, features)),
                'proba': {k: float(v) for k, v in zip(status_map.values(), proba)}
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'recommended_actions': 'Check system configuration',
                'explanation': 'Failed to analyze compliance'
            }

    def get_recommendations(self, pred_class, software_list):
        recommendations = {
            0: [
                "Update operating system to latest version",
                "Remove unauthorized software",
                "Review security settings",
                "Run full antivirus scan"
            ],
            1: [
                "Check for software updates",
                "Review system configuration",
                "Monitor for unusual activity",
                "Schedule follow-up scan"
            ],
            2: [
                "Continue regular maintenance",
                "Schedule next compliance check",
                "Review security best practices"
            ]
        }

        # Add specific software recommendations
        if pred_class in [0, 1]:
            blocked = [
                s for s in software_list
                if any(kw in s['name'].lower()
                       for kw in ['crack', 'hack', 'keygen'])
            ]
            if blocked:
                recommendations[pred_class].insert(
                    0,
                    f"Remove potentially harmful software: {', '.join(s['name'] for s in blocked)}"
                )

        return "\n".join(recommendations.get(pred_class, []))

    def generate_explanation(self, features, pred_class):
        explanations = {
            0: (
                "Device has critical compliance issues including: "
                f"{'outdated OS ' if features[2] > 30 else ''}"
                f"{'blocked software ' if features[4] > 0 else ''}"
                f"{'poor compliance history ' if features[5] < 0.5 else ''}"
                f"(Risk score: {1 - features[5]:.1f}/1.0)"
            ),
            1: (
                "Device shows some risk factors: "
                f"{'moderately outdated ' if 15 < features[2] <= 30 else ''}"
                f"{'slightly poor compliance history ' if 0.5 <= features[5] < 0.7 else ''}"
                f"(Risk score: {0.5 - (features[5] - 0.5):.1f}/1.0)"
            ),
            2: (
                "Device meets all critical compliance requirements "
                f"(Risk score: {features[5]:.1f}/1.0)"
            )
        }
        return explanations.get(pred_class, "Compliance status could not be determined")

    @transaction.atomic
    def train_model(self, X, y, test_size=0.2):
        """Method to train or retrain the model with new data"""
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=test_size,
                random_state=42,
                stratify=y
            )

            # Train model
            self.model.fit(X_train, y_train)

            # Evaluate
            report = classification_report(y_test, self.model.predict(X_test))

            # Feature importances
            importances = dict(zip(self.features, self.model.feature_importances_))

            # Save training data for future reference
            self._save_training_data(X, y)

            self.save_model()
            return {
                'report': report,
                'importances': importances,
                'accuracy': self.model.score(X_test, y_test)
            }
        except Exception as e:
            raise RuntimeError(f"Training failed: {str(e)}")

    def _save_training_data(self, X, y):
        """Append training data to CSV file"""
        with open(TRAINING_DATA_PATH, 'a') as f:
            for features, label in zip(X, y):
                f.write(','.join(map(str, features + [label])) + '\n')

    def load_training_data(self):
        """Load training data from CSV"""
        if not os.path.exists(TRAINING_DATA_PATH):
            return None, None

        df = pd.read_csv(TRAINING_DATA_PATH)
        X = df[self.features].values
        y = df['label'].values
        return X, y

    def retrain_model(self):
        """Retrain model with accumulated data"""
        X, y = self.load_training_data()
        print(self.load_training_data())
        # Check if data is loaded
        if X is None or y is None:
            return {"status": "skipped", "reason": "Training data could not be loaded."}

        # Convert to numpy arrays if needed
        X = np.array(X)
        y = np.array(y)

        # Remove rows where y is NaN
        mask = ~np.isnan(y)
        X = X[mask]
        y = y[mask]

        # Optionally remove rows where X has NaNs too
        if np.isnan(X).any():
            valid_rows = ~np.isnan(X).any(axis=1)
            X = X[valid_rows]
            y = y[valid_rows]

        # Ensure enough data remains
        if len(X) < 50:
            return {"status": "skipped",
                    "reason": f"Not enough valid training samples after cleaning. Only {len(X)} left."}

        return self.train_model(X, y)
