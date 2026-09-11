import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from sapl.painel.apps import AppConfig as PainelAppConfig
from sapl.sessao.models import SessaoPlenaria

logger = logging.getLogger(__name__)


class _ScopeRequest:
    """
    Adaptador mínimo para reaproveitar build_dados_painel(request, pk) —
    que lê request.user/request.session para o cronômetro — a partir do
    scope de uma conexão WebSocket, que não é um HttpRequest de verdade.
    AuthMiddlewareStack (usado em sapl/asgi.py) já popula scope['user'] e
    scope['session'] a partir do cookie de sessão, então isso é só leitura,
    igual ao que get_cronometro_status já fazia.
    """

    def __init__(self, scope):
        self.user = scope['user']
        self.session = scope['session']


class PainelConsumer(AsyncJsonWebsocketConsumer):
    """
    Um grupo por SessaoPlenaria (`sessao_<id>`) — painel público, tela de
    voto individual (tablet) e tela de registro do operador conectam todos
    aqui e recebem o mesmo payload completo (broadcast de estado inteiro,
    não deltas — ver Parte 3 do plano de migração polling->push).
    """

    async def connect(self):
        self.sessao_id = self.scope['url_route']['kwargs']['sessao_id']
        user = self.scope['user']

        if not user.is_authenticated:
            await self.close(code=4401)
            return

        if not await self._user_pode_conectar(user):
            await self.close(code=4403)
            return

        if not await self._sessao_existe(self.sessao_id):
            await self.close(code=4404)
            return

        self.group_name = 'sessao_{}'.format(self.sessao_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        payload = await self._build_dados_painel(self.sessao_id)
        await self.send_json({'type': 'data', 'payload': payload})

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get('type') == 'ping':
            await self.send_json({'type': 'pong'})

    async def data(self, event):
        await self.send_json({'type': 'data', 'payload': event['payload']})

    @database_sync_to_async
    def _build_dados_painel(self, sessao_id):
        # import local para evitar ciclo de import no carregamento do ASGI
        # (sapl.painel.views importa vários modelos/decorators de request
        # HTTP que não precisam existir antes do Django estar totalmente
        # pronto, o que já é garantido aqui por database_sync_to_async
        # rodar depois de django.setup() em sapl/asgi.py).
        from sapl.painel.views import build_dados_painel
        return build_dados_painel(_ScopeRequest(self.scope), sessao_id)

    @database_sync_to_async
    def _user_pode_conectar(self, user):
        """
        Aceita qualquer usuário que já teria acesso a alguma das três telas
        que este consumer substitui — não há um único modelo de permissão,
        já que painel público, vereador votando e operador registrando têm
        gates diferentes hoje: check_permission do módulo painel (usado por
        get_dados_painel), parlamentares.can_vote (usado por votante_view),
        e permissão do módulo sessao (usado por SessaoPermissionMixin na
        tela de registro do operador). Substitui o stub `return True` da
        referência em feat/painel-votacao-v2.
        """
        if user.has_module_perms(PainelAppConfig.label):
            return True
        if user.has_perm('parlamentares.can_vote'):
            return True
        if user.has_module_perms('sessao'):
            return True
        return False

    @database_sync_to_async
    def _sessao_existe(self, sessao_id):
        return SessaoPlenaria.objects.filter(id=sessao_id).exists()
