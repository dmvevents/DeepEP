"""
Celery configuration for async task processing
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('mortgage_calculator')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Periodic tasks configuration
app.conf.beat_schedule = {
    'check-stale-tax-data': {
        'task': 'scraper_integration.tasks.check_stale_tax_data',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
    'cleanup-old-documents': {
        'task': 'documents.tasks.cleanup_old_documents',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Weekly on Sunday at 3 AM
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
