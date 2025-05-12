from django.core.management.base import BaseCommand
from django.utils import timezone
import numpy as np
from collections import Counter
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train and manage AI models for compliance monitoring'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            default='initialize',
            choices=['initialize', 'retrain', 'evaluate'],
            help='Action to perform: initialize (default), retrain, or evaluate'
        )
        parser.add_argument(
            '--samples',
            type=int,
            default=1000,
            help='Number of synthetic samples to generate for initialization'
        )

    def handle(self, *args, **options):
        mode = options['mode']
        samples = options['samples']

        try:
            if mode == 'initialize':
                self.initialize_models(samples)
            elif mode == 'retrain':
                self.retrain_with_real_data()
            elif mode == 'evaluate':
                self.evaluate_models()

            self.stdout.write(self.style.SUCCESS(f"Successfully completed {mode} operation"))
        except Exception as e:
            logger.error(f"Failed to {mode} models: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error during {mode}: {str(e)}"))

    def initialize_models(self, n_samples):
        """Initialize AI models with synthetic data"""
        from management.ai.compliance_analyzer import ComplianceAnalyzer
        from management.ai.anomaly_detector import AnomalyDetector

        self.stdout.write(f"Initializing models with {n_samples} synthetic samples...")

        # Generate synthetic compliance data
        X_comp, y_comp = self.generate_compliance_data(n_samples)

        # Initialize and train compliance model
        comp_analyzer = ComplianceAnalyzer()
        comp_analyzer.train_model(X_comp, y_comp)

        # Generate synthetic anomaly data
        X_anom = self.generate_anomaly_data(n_samples)

        # Initialize and train anomaly detector
        anomaly_detector = AnomalyDetector()
        anomaly_detector.model.fit(X_anom)  # Anomaly detection is unsupervised

        self.stdout.write(self.style.SUCCESS(
            f"Initialized models with synthetic data\n"
            f"Compliance classes: {Counter(y_comp)}\n"
            f"Anomaly samples: {len(X_anom)}"
        ))

    def retrain_with_real_data(self):
        """Retrain models with real data from the database"""
        from management.ai.compliance_analyzer import ComplianceAnalyzer
        from management.models import Device, ActivityReport
        import numpy as np

        self.stdout.write("Retraining models with real data...")

        devices = Device.objects.all().prefetch_related('installedsoftware')
        if not devices.exists():
            raise ValueError("No devices found in database")

        # Prepare compliance training data
        X_comp = []
        y_comp = []
        comp_analyzer = ComplianceAnalyzer()

        for device in devices:
            try:
                software_list = list(device.installedsoftware.all().values('name', 'version', 'publisher'))
                historical_reports = list(ActivityReport.objects.filter(device=device).values())

                features = comp_analyzer.preprocess_data({
                    'os': device.os,
                    'device_type': device.device_type,
                    'last_scan': device.last_scan,
                    'historical_reports': historical_reports
                }, software_list)

                status_map = {'non-compliant': 0, 'warning': 1, 'compliant': 2}
                label = status_map.get(device.status, 0)

                X_comp.append(features)
                y_comp.append(label)
            except Exception as e:
                logger.warning(f"Skipping device {device.id} due to error: {str(e)}")
                continue

        # Train compliance model
        if len(X_comp) > 10:  # Minimum samples required
            comp_analyzer.train_model(np.array(X_comp), np.array(y_comp))
            self.stdout.write(f"Retrained compliance model with {len(X_comp)} samples")
        else:
            self.stdout.write(self.style.WARNING(
                "Insufficient real data for compliance model (need >10 samples)"
            ))

    def evaluate_models(self):
        """Evaluate model performance"""
        from management.ai.compliance_analyzer import ComplianceAnalyzer
        from sklearn.model_selection import cross_val_score

        self.stdout.write("Evaluating model performance...")

        # Load compliance model
        comp_analyzer = ComplianceAnalyzer()

        # Generate evaluation data
        X, y = self.generate_compliance_data(500)

        # Cross-validate
        scores = cross_val_score(
            comp_analyzer.model, X, y,
            cv=5, scoring='f1_weighted'
        )

        self.stdout.write(self.style.SUCCESS(
            f"Compliance model evaluation:\n"
            f"F1 scores: {scores}\n"
            f"Mean F1: {np.mean(scores):.2f} (±{np.std(scores):.2f})"
        ))

    def generate_compliance_data(self, n_samples=1000):
        """Generate realistic synthetic compliance data"""
        # OS type (1=Windows, 2=macOS, 3=Linux, 4=Other)
        os_type = np.random.choice([1, 2, 3, 4], size=n_samples, p=[0.6, 0.2, 0.15, 0.05])

        # Device type (1=laptop, 2=desktop, 3=mobile, 4=server)
        device_type = np.random.choice([1, 2, 3, 4], size=n_samples, p=[0.5, 0.3, 0.15, 0.05])

        # Days since last scan
        days_since = np.where(
            np.random.random(n_samples) > 0.7,
            np.random.randint(30, 90, size=n_samples),  # Non-compliant
            np.random.randint(1, 14, size=n_samples)  # Compliant
        )

        # Number of installed software
        num_software = np.random.poisson(15, size=n_samples)

        # Number of blocked software
        num_blocked = np.random.binomial(5, 0.1, size=n_samples)

        # Percentage compliance history
        pct_compliant = np.clip(np.random.beta(2, 2, size=n_samples), 0, 1)

        # Combine features
        X = np.column_stack([os_type, device_type, days_since, num_software, num_blocked, pct_compliant])

        # Generate labels (0=non-compliant, 1=warning, 2=compliant)
        y = np.zeros(n_samples, dtype=int)

        # Compliant devices
        compliant_mask = (num_blocked == 0) & (days_since <= 7) & (pct_compliant > 0.7)
        y[compliant_mask] = 2

        # Warning devices
        warning_mask = ((num_blocked == 0) &
                        ((days_since <= 30) | (pct_compliant > 0.5)) &
                        ~compliant_mask)
        y[warning_mask] = 1

        return X, y

    def generate_anomaly_data(self, n_samples=1000):
        """Generate synthetic anomaly detection data"""
        # Normal device features
        X_normal = np.column_stack([
            np.random.choice([1, 2, 3], size=n_samples),  # OS
            np.random.poisson(15, size=n_samples),  # Software count
            np.random.choice([0, 1, 2], size=n_samples),  # Status
            np.random.randint(1, 30, size=n_samples),  # Scan age
            np.random.choice([0, 1], size=n_samples)  # User role
        ])

        # Add some anomalies (5% of data)
        n_anomalies = int(n_samples * 0.05)
        X_anomalies = np.column_stack([
            np.random.choice([4, 5], size=n_anomalies),  # Rare OS
            np.random.poisson(30, size=n_anomalies),  # High software count
            np.full(n_anomalies, 2),  # Non-compliant status
            np.random.randint(60, 365, size=n_anomalies),  # Old scans
            np.full(n_anomalies, 2)  # Unknown role
        ])

        return np.vstack([X_normal, X_anomalies])