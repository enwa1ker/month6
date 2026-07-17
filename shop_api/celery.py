import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_api.settings')

app = Celery('shop_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.timezone = settings.TIME_ZONE
app.conf.beat_schedule = {
    'delete-old-task-files-every-night': {
        'task': 'users.tasks.delete_old_task_files',
        'schedule': crontab(hour=3, minute=0),
    },
}
