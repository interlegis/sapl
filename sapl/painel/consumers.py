import json
from channels.generic.websocket import WebsocketConsumer


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        print('conectado ao ws')

    def disconnect(self, close_code):
        print('desconectado ao ws')
        pass

    def receive(self, text_data):
        print('receive message')
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        self.send(text_data=json.dumps({
            'message': message
        }))