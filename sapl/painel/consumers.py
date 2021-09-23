import json
import requests
from channels.generic.websocket import AsyncJsonWebsocketConsumer



class PainelConsumer(AsyncJsonWebsocketConsumer):
    async def connect (self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        print('Received Message')

        print('Enviando...')
        url_dados = 'http://localhost:8000/painel/786/dados'

        #response = requests.get(url_dados)
        #print(response)

        await self.send_json({
            'message': 'teste'
        })

    async def send(self, event):
        print('Entrou')
    