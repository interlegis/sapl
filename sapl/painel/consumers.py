import json
import requests
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from sapl.painel import views


class PainelConsumer(AsyncJsonWebsocketConsumer):
    async def connect (self):
        print('Conectado')
        await self.channel_layer.group_add('painel', self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard('painel', self.channel_name)

    async def receive (self, text_data):
        json_data = views.get_dados_painel(text_data)
        await self.send(json.dumps(json_data))

    async def send_data(self, event):
        new_data = event['message']
        await self.send(json.dumps(new_data))
    