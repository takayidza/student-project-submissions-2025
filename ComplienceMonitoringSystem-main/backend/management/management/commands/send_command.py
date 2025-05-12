# management/commands/send_command.py
from django.core.management.base import BaseCommand
from management.utils import send_monitoring_command

class Command(BaseCommand):
    help = 'Send a command to monitoring clients'

    def add_arguments(self, parser):
        parser.add_argument('command', type=str, help='Command to send to clients')

    def handle(self, *args, **options):
        command = options['command']
        self.stdout.write(f"Sending command: {command}")
        send_monitoring_command(command)
        self.stdout.write("Command sent to all connected clients")