from celery import shared_task
from urllib import request

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from sapl.painel import views

channel_layer = get_channel_layer()

@shared_task
def get_dados_painel_celery():
    json_data = views.get_dados_painel(786)
    async_to_sync(channel_layer.group_send)('painel', {'type':'send_data', 'message': json_data})
