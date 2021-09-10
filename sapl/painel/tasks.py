import json
import requests
import urllib

from celery import shared_task


@shared_task
def get_cronometro():
    url_dados = 'http://localhost:8000/painel/1272/dados'
    # print(requests.get(url_dados).status_code)
    #response = requests.get(url_dados)
    response = urllib.request.urlopen(url_dados)
    dados = json.loads(response.read())
    #cronometro = response['sessao_plenaria']['cronometro_discurso']
    print(dados)
    print(response)
    print(response.encoding)
    return response
