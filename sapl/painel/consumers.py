import json
import requests
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from sapl.sessao.models import (ExpedienteMateria, OradorExpediente, OrdemDia,
                                PresencaOrdemDia, RegistroVotacao,
                                SessaoPlenaria, SessaoPlenariaPresenca,
                                VotoParlamentar, RegistroLeitura)


class PainelConsumer(AsyncJsonWebsocketConsumer):
    async def connect (self):
        print('Conectado')
        await self.accept()

    async def disconnect(self, close_code):
        print('Disconectado:', close_code)
        pass

    async def join_group(self):
        print('Group')
        await self.channel_layer.group_add('painel', self.channel_name)

    async def receive(self, text_data):
        print('Received Message:' + text_data)

        await self.send_data(786)

    async def send_data(self, id):
        sessao = SessaoPlenaria.objects.get(id=id)

        response = {
            'sessao_plenaria': str(sessao),
            'sessao_plenaria_data': sessao.data_inicio.strftime('%d/%m/%Y'),
            'sessao_plenaria_hora_inicio': sessao.hora_inicio,
            'sessao_solene': sessao.tipo.nome == "Solene",
            'sessao_finalizada': sessao.finalizada,
            'tema_solene': sessao.tema_solene,
            'status_painel': sessao.painel_aberto,
        }
        await self.send_json(response)
    