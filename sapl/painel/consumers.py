import json
import requests
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from sapl.painel import views


class PainelConsumer(AsyncJsonWebsocketConsumer):
    async def connect (self):
        print('Conectado')
        await self.accept()

    async def disconnect(self, close_code):
        print('Desconectado:', close_code)
        pass

    async def receive(self, text_data):

        await self.send_data(786)

    async def send_data(self, id):
        response = views.get_dados_painel(id)

        await self.send_json(response)
    