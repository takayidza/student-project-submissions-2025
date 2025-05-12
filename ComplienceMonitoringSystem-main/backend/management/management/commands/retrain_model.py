from django.core.management.base import BaseCommand
from management.ml.compliance_analyzer import ComplianceAnalyzer


class Command(BaseCommand):
    help = 'Retrain the compliance model with accumulated data'

    def handle(self, *args, **options):
        analyzer = ComplianceAnalyzer()
        result = analyzer.retrain_model()

        if result.get('status') == 'skipped':
            self.stdout.write(self.style.WARNING(result['reason']))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Model retrained\nAccuracy: {result['accuracy']:.1%}\n" +
                f"Classification Report:\n{result['report']}"
            ))