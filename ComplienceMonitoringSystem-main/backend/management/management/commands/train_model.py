from django.core.management.base import BaseCommand

from management.ml.ai_data_generater import generate_training_data
from management.ml.compliance_analyzer import ComplianceAnalyzer
import numpy as np


class Command(BaseCommand):
    help = 'Train the compliance prediction model'

    def handle(self, *args, **options):
        analyzer = ComplianceAnalyzer()

        # Generate 1 million rows of synthetic training data
        df = generate_training_data(1_000_000)
        X = df.drop(columns='label').values
        y = df['label'].values

        result = analyzer.train_model(X, y)
        self.stdout.write(self.style.SUCCESS(
            f"Model trained successfully\nAccuracy: {result['accuracy']:.1%}\n" +
            f"Classification Report:\n{result['report']}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Model trained successfully\nAccuracy: {result['accuracy']:.1%}\n" +
            f"Classification Report:\n{result['report']}"
        ))