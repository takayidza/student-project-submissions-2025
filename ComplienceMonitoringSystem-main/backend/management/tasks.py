# myapp/tasks.py
from celery import shared_task
import time

from management.scanners.compliance_scanner import scan_all_devices


@shared_task
def add(x, y):
    time.sleep(5)  # Simulate some work
    return x + y

@shared_task
def send_welcome_email(user_email):
    time.sleep(10)  # Simulate sending an email
    print(f"Welcome email sent to {user_email}")
    # In a real application, you would use Django's email sending functionality here

# myapp/tasks.py
from celery import shared_task
import time

@shared_task
def periodic_test_task():
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"Periodic test task executed at: {current_time} (in test environment)")
    # You can add more complex logic here for your testing purposes

@shared_task
def scan_all_devices_schedule():
    scan_all_devices()