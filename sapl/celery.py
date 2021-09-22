import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sapl.settings')

app = Celery('sapl')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'get_cronometro_inst': {
        'task': 'sapl.painel.tasks.get_cronometro',
        'schedule': 1.0
    }
}

app.autodiscover_tasks()
