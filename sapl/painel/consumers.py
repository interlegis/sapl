import json
import json
import logging
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer

from sapl.base.models import CasaLegislativa, AppConfig
from sapl.sessao.models import SessaoPlenaria, SessaoPresencasView, \
    SessaoOradoresView, SessaoMateriasVotacoesView


def get_materia_votacao(votacao):
    return {
        # TOO UGLY! FIX THIS if-else
        "materia_id": votacao.materia.id if votacao and votacao.materia else "",
        "texto": str(votacao.materia) if votacao and votacao.materia else "",
        "ementa": votacao.materia.ementa if votacao and votacao.materia and votacao.materia.ementa else "",
        "resultado": {
            "resultado_votacao": votacao.resultado_votacao if votacao and votacao.resultado_votacao else "",
            "resultado": votacao.resultado if votacao and votacao.resultado else "",
            "numero_votos": votacao.numero_votos if votacao and votacao.numero_votos else {},
            "votos_parlamentares": votacao.votos_parlamentares if votacao and votacao.votos_parlamentares else [],
        },
    }


def get_dados_painel(sessao_plenaria_id: int) -> dict:
    app_config = AppConfig.objects.first()
    sessao = SessaoPlenaria.objects.get(id=sessao_plenaria_id)
    casa = CasaLegislativa.objects.first()
    brasao = casa.logotipo.url \
        if app_config.mostrar_brasao_painel else None

    # Painel
    # TODO: recuperar outra matéria quando não existir nenhuma materia_votacao aberta!
    materia_votacao = SessaoMateriasVotacoesView.objects. \
        filter(sessao_plenaria_id=sessao_plenaria_id, votacao_aberta=True).first()

    if not materia_votacao:
        return {
            "type": "data",
            "sessao_aberta": sessao.iniciada and not sessao.finalizada,
            "painel_aberto": sessao.painel_aberto,
            "mostrar_voto": app_config.mostrar_voto,
            "message": "PAINEL ENCONTRA-SE FECHADO" if not sessao.painel_aberto else "",
            "sessao": {
                "sessao_plenaria_id": sessao.id,
                "brasao": brasao,
                "sessao_plenaria": str(sessao),
                "sessao_plenaria_data": sessao.data_inicio.strftime("%d/%m/%Y"),
                "sessao_plenaria_hora_inicio": sessao.hora_inicio,
                "sessao_solene": sessao.tipo.nome == "Solene",
                "sessao_finalizada": sessao.finalizada,
                "tema_solene": sessao.tema_solene,
            },
            "message": "Nenhuma matéria aberta para votação!",
        }

    presentes = SessaoPresencasView.objects.filter(sessao_plenaria_id=sessao_plenaria_id,
                                                   etapa_sessao=materia_votacao.etapa_sessao,
                                                   ativo=True).values_list(
        'parlamentar_id',
        'nome_parlamentar',
        'filiacao', )
    parlamentares = [dict(zip(['parlamentar_id', 'nome_parlamentar', 'filiacao'], p)) for p in presentes]

    # Adicionar fotografia dos parlamentares
    from sapl.parlamentares.models import Parlamentar
    from image_cropping.utils import get_backend
    parlamentar_ids = [p['parlamentar_id'] for p in parlamentares]
    parlamentares_db = {p.id: p for p in Parlamentar.objects.filter(id__in=parlamentar_ids)}
    for p in parlamentares:
        par = parlamentares_db.get(p['parlamentar_id'])
        if par and par.fotografia:
            try:
                p['fotografia'] = get_backend().get_thumbnail_url(
                    par.fotografia,
                    {
                        'size': (128, 128),
                        'box': par.cropping,
                        'crop': True,
                        'detail': True,
                    }
                )
            except Exception:
                p['fotografia'] = None
        else:
            p['fotografia'] = None
    if materia_votacao and materia_votacao.numero_votos:
        materia_votacao.numero_votos.update({"num_presentes": len(parlamentares)})

    oradores = SessaoOradoresView.objects.filter(sessao_plenaria_id=sessao_plenaria_id,
                                                 etapa_sessao=materia_votacao.etapa_sessao).values_list(
        'ordem_pronunciamento',
        'nome_parlamentar',
    )
    oradores = [dict(zip(['ordem_pronunciamento', 'nome_parlamentar'], o)) for o in oradores]

    # TODO: recover stopwatch state from DB/Cache
    stopwatch = {
        "type": "stopwatch.state",
        "id": "sw:main",
        "status": "running",  # "running" | "paused" | "stopped"
        "started_at_ms": 1699990000123,  # epoch ms when (re)started
        "elapsed_ms": 5320
    }

    dados_sessao = {
        "type": "data",
        "sessao_aberta": sessao.iniciada and not sessao.finalizada,
        "painel_aberto": sessao.painel_aberto,
        "mostrar_voto": app_config.mostrar_voto,
        "message": "PAINEL ENCONTRA-SE FECHADO" if not sessao.painel_aberto else "",
        "sessao": {
            "sessao_plenaria_id": sessao.id,
            "brasao": brasao,
            "sessao_plenaria": str(sessao),
            "sessao_plenaria_data": sessao.data_inicio.strftime("%d/%m/%Y"),
            "sessao_plenaria_hora_inicio": sessao.hora_inicio,
            "sessao_solene": sessao.tipo.nome == "Solene",
            "sessao_finalizada": sessao.finalizada,
            "tema_solene": sessao.tema_solene,
        },
        "parlamentares": parlamentares,
        "oradores": oradores,
        "materia": get_materia_votacao(materia_votacao),
        "stopwatch": [stopwatch],  # TODO: array of stopwatches
    }

    print(json.dumps(dados_sessao, indent=4))
    return dados_sessao


class PainelConsumer(AsyncJsonWebsocketConsumer):
    logger = logging.getLogger(__name__)

    # def __init__(self):
    #     self.group = set()
    #     self.controller_id = None

    async def connect(self):
        # TODO: transformar prints em log messages
        user = self.scope.get("user")
        controller_id = self.scope["url_route"]["kwargs"]["controller_id"]
        print(f"user: {user}, controller_id: {controller_id}")

        if not (user and user.is_authenticated):
            self.logger.info(f"{user} is not authenticated user!")
            await self.close(code=4401)  # explicit, graceful close
            return

        if not await self.user_can_view(user.id, controller_id):
            await self.close(code=4403)
            return

        self.controller_id = controller_id
        self.group = f"controller_{controller_id}"
        print(self.group)
        await self.channel_layer.group_add(self.group, self.channel_name)

        await self.accept()
        # await self.send_json({"type": "data",
        #                        "text": "Connection established!"})

        print("SENDING bootstrap DATA DO CONSUMER ")
        print(get_dados_painel(controller_id))
        await self.send_json(get_dados_painel(controller_id))

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    # Called by server via channel_layer.group_send
    # async def notify(self, event):
    #     # event: {"type": "notify", "data": {...}}
    #     await self.send_json(event)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data or "{}")
        print("Received from client:", data)  # TODO: turn into log messages
        msg_type = data.get("type")
        if msg_type == "ping":
            print("PING")
            await self.send_json({"type": "ping", "ts": time.time()})
            return
        elif msg_type == "echo":
            await self.send_json(data)
            return
        elif msg_type == "stopwatch.state":
            print(data)
            return
        await self.send_json({"type": "error", "message": "Misformed message"})
        return

    async def stopwatch_update(self, event):
        await self.send_json(event)
        return

    @database_sync_to_async
    def user_can_view(self, user_id, controller_id) -> bool:
        # Replace with your ACL check (ORM must be in a sync wrapper)
        # return Controller.objects.filter(id=controller_id, owners__id=user_id).exists()
        return True


class HealthConsumer(AsyncWebsocketConsumer):
    """
        WebSockets consumer that doesn"t require authentication to
        debug with wscat (wscat -c ws://127.0.0.1:8000/ws/painel/)
    """
    logger = logging.getLogger(__name__)

    async def connect(self):
        try:
            await self.accept()
            await self.send(json.dumps({"ok": True}))
        except Exception as e:
            self.logger.exception("connect failed: %s", e)
            # Let Channels close with 1011 if we got here

    async def receive(self, text_data=None, bytes_data=None):
        await self.send(text_data or "")
