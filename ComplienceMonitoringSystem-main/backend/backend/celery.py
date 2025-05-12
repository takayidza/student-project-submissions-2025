from celery.schedules import crontab, schedule
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

app.conf.beat_schedule = {
    'populate_grades_classes_every_year': {
        'task': 'apps.student.tasks.run_grade_and_class_population',
        'schedule': crontab(minute=0, hour=0, day_of_month=1, month_of_year=1),
    },
    'create_learning_classes_every_year': {
        'task': 'apps.student.tasks.run_learning_class_creation',
        'schedule': crontab(minute=10, hour=0, day_of_month=1, month_of_year=1),
    },
    'create_attendance_records_daily': {
        'task': 'apps.student.tasks.create_daily_attendance_records',
        'schedule': schedule(3.0),  # Every day at midnight  crontab(minute=0, hour=0)
    },
    'create-new-academic-year': {
        'task': 'apps.academic.tasks.create_new_academic_year',
        'schedule': '0 0 1 1 *',  # run on January 1st every year at midnight
    },

}
