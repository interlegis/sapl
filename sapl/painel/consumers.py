import json
from channels.generic.websocket import WebsocketConsumer


class PainelConsumer(WebsocketConsumer):
    def connect(self):
        self.channel_layer.group_add('message', self.channel_name)
        self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('message', self.channel_name)

    def receive(self, text_data):
        print('receive message')
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        self.send(text_data=json.dumps({
            'message': message
        }))
        
    async def send(self, event):
        new_data = event['text']
        print(new_data)
        await self.send(json.dumps(new_data))