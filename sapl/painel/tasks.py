from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from sapl.painel import views

channel_layer = get_channel_layer()

def get_dados_painel_final(id):
    json_data = views.get_dados_painel(id)
    async_to_sync(channel_layer.group_send)('painel', {'type':'send_data', 'message': json_data})
