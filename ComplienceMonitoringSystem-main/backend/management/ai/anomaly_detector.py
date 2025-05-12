# ai/anomaly_detector.py
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib
from pathlib import Path
import os
from datetime import datetime

MODEL_PATH = Path(__file__).parent / 'models' / 'anomaly_model.joblib'
SCALER_PATH = Path(__file__).parent / 'models' / 'anomaly_scaler.joblib'


class AnomalyDetector:
    def __init__(self, contamination=0.05):
        self.model = None
        self.scaler = None
        self.contamination = contamination
        self.features = [
            'os_type', 'software_count', 'status_code',
            'scan_age_days', 'user_role_code'
        ]
        self.load_models()

    def load_models(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
        else:
            self.scaler = StandardScaler()
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=200
            )

    def save_models(self):
        os.makedirs(MODEL_PATH.parent, exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.scaler, SCALER_PATH)

    def detect(self, current_data, peer_data):
        """Enhanced anomaly detection with feature engineering"""
        if not peer_data:
            return {
                'is_anomaly': False,
                'reason': 'No peer data available',
                'score': 0.0
            }

        try:
            # Convert all data to features
            current_features = self._extract_features(current_data)
            peer_features = np.array([self._extract_features(p) for p in peer_data])

            # Fit models if not fitted
            if not hasattr(self.scaler, 'mean_'):
                self.scaler.fit(peer_features)
                peer_scaled = self.scaler.transform(peer_features)
                self.model.fit(peer_scaled)
                self.save_models()
            else:
                peer_scaled = self.scaler.transform(peer_features)

            # Scale current data
            current_scaled = self.scaler.transform([current_features])

            # Predict anomaly
            is_anomaly = self.model.predict(current_scaled)[0] == -1
            anomaly_score = float(self.model.decision_function(current_scaled)[0])

            return {
                'is_anomaly': bool(is_anomaly),
                'score': anomaly_score,
                'description': self._generate_description(current_features, peer_features),
                'features': dict(zip(self.features, current_features))
            }

        except Exception as e:
            return {
                'is_anomaly': False,
                'error': str(e),
                'score': 0.0
            }

    def _extract_features(self, data):
        """Convert device data to feature vector with enhanced encoding"""
        # OS encoding
        os_mapping = {
            'windows': 1,
            'mac': 2,
            'linux': 3,
            'ubuntu': 3,
            'debian': 3,
            'android': 4,
            'ios': 5,
            'other': 6
        }
        os_type = next(
            (v for k, v in os_mapping.items() if k in data['os'].lower()),
            6  # other
        )

        # Status encoding
        status_map = {
            'compliant': 0,
            'warning': 1,
            'non-compliant': 2
        }
        status_code = status_map.get(data['status'].lower(), 1)

        # User role encoding
        role_map = {
            'admin': 0,
            'user': 1,
            'unknown': 2
        }
        user_role_code = role_map.get(data.get('user_role', 'unknown').lower(), 2)

        return np.array([
            os_type,
            data['software_count'],
            status_code,
            data['last_scan_age'],
            user_role_code
        ])

    def _generate_description(self, current, peers):
        """Generate detailed anomaly explanation"""
        peer_avg = np.mean(peers, axis=0)
        deviations = current - peer_avg

        reasons = []
        if abs(deviations[0]) > 1:  # OS difference
            os_types = {
                1: 'Windows',
                2: 'macOS',
                3: 'Linux',
                4: 'Android',
                5: 'iOS',
                6: 'Other OS'
            }
            reasons.append(
                f"unusual OS type ({os_types.get(int(current[0]), 'unknown')} "
                f"vs peers average {os_types.get(int(peer_avg[0]), 'unknown')})"
            )

        if deviations[1] > peer_avg[1] * 0.3:  # Software count
            reasons.append(
                f"high software count ({int(current[1])} vs peer average {int(peer_avg[1])})"
            )

        if deviations[2] > 0:  # Status
            statuses = {
                0: 'compliant',
                1: 'warning',
                2: 'non-compliant'
            }
            reasons.append(
                f"worse status ({statuses.get(int(current[2]), 'unknown')} "
                f"vs peers average {statuses.get(int(peer_avg[2]), 'unknown')})"
            )

        if deviations[3] > 7:  # Scan age
            reasons.append(
                f"outdated scan ({int(current[3])} days old vs peer average {int(peer_avg[3])} days)"
            )

        return "Anomaly detected due to: " + ", ".join(reasons) if reasons else "Statistical anomaly"