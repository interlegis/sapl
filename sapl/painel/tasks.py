import json
import requests
import urllib

from celery import shared_task

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

@shared_task
def get_cronometro():
    url_dados = 'http://localhost:8000/painel/786/dados'


    login_data = {'username': 'sapl', 'password': 'sapl'}
    with requests.Session() as session:
        session.get('http://localhost:8000/login/')
        csrftoken = session.cookies['csrftoken']
        login_data['csrfmiddlewaretoken'] = csrftoken
        post = session.post('http://localhost:8000/login/', data=login_data)
        if post.ok: print('conexao realizada com sucesso')
        r = session.get('http://localhost:8000/painel/786/dados')
        json_data = r.json()
        print(json_data)

    async_to_sync(channel_layer.group_send)('message', {'type':'send', 'text': json_data})
