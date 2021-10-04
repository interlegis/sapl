import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sapl.settings')

app = Celery('sapl')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'get_dados_inst': {
        'task': 'sapl.painel.tasks.get_dados_painel_celery',
        'schedule': 0.2
    }
}

app.autodiscover_tasks()