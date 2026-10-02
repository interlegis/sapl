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
    aqui. O snapshot é sempre completo (não deltas — ver Parte 3 do plano
    de migração polling->push), mas não é mais idêntico para todo mundo:
    cada conexão pede o seu próprio a cada aviso de mudança (ver
    painel_refresh()), com o voto mascarado ou não conforme o papel de
    quem está conectado (self.is_operator) — o grupo em si nunca carrega
    o voto real, só um sinal de "algo mudou".
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

        # Papéis calculados uma vez, na conexão — reaproveitados em todo
        # refresh subsequente sem reconsultar as permissões do usuário.
        self.is_operator = await self._is_operator(user)
        self.can_cast_vote = await self._can_cast_vote(user)

        self.group_name = 'sessao_{}'.format(self.sessao_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        payload = await self._build_dados_painel(self.sessao_id)
        await self.send_json({'type': 'data', 'payload': payload})

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg_type = content.get('type')
        if msg_type == 'ping':
            await self.send_json({'type': 'pong'})
        elif msg_type == 'vote':
            await self._handle_vote(content)
        elif msg_type == 'registro_toggle':
            await self._handle_registro_toggle(content)

    async def data(self, event):
        # Ainda aceito por compatibilidade (não é mais como
        # broadcast_dados_painel() manda algo pro grupo, mas nada impede
        # outro caller de enviar um group_send neste formato).
        await self.send_json({'type': 'data', 'payload': event['payload']})

    async def painel_refresh(self, event):
        """
        Handler do sinal leve que broadcast_dados_painel() manda pro grupo
        (`{"type": "painel.refresh"}` — Channels troca o "." por "_" no
        nome do método). Cada conexão reconsulta o snapshot por conta
        própria e manda só pra si mesma: é aqui, não no group_send, que o
        voto real fica restrito a quem tem self.is_operator.
        """
        payload = await self._build_dados_painel(self.sessao_id)
        await self.send_json({'type': 'data', 'payload': payload})

    async def _handle_vote(self, content):
        if not getattr(self, 'can_cast_vote', False):
            await self.send_json({
                'type': 'vote_error',
                'message': 'Seu usuário não tem permissão para registrar votos.'})
            return

        parlamentar_id = content.get('parlamentar_id')
        voto = content.get('voto')
        try:
            result = await self._cast_vote(parlamentar_id, voto)
        except Exception as e:
            await self.send_json({'type': 'vote_error', 'message': str(e)})
            return

        await self.send_json({'type': 'vote_ack', **result})
        # Sinal pro grupo inteiro (inclusive esta conexão) reconsultar —
        # não manda o payload aqui: quem recebe decide seu próprio
        # mostrar_voto em painel_refresh().
        await self.channel_layer.group_send(self.group_name, {'type': 'painel.refresh'})

    async def _handle_registro_toggle(self, content):
        """
        Equivalente ao bloquear-registro-votacao/reabrir-votacao de
        nominal.html — mesmo gate de permissão do voto (can_cast_vote),
        já que é a mesma Mesa/operador que faz as duas coisas.
        """
        if not getattr(self, 'can_cast_vote', False):
            await self.send_json({
                'type': 'registro_toggle_error',
                'message': 'Seu usuário não tem permissão para esta ação.'})
            return

        aberto = bool(content.get('aberto'))
        try:
            result = await self._toggle_registro(aberto)
        except Exception as e:
            await self.send_json({'type': 'registro_toggle_error', 'message': str(e)})
            return

        await self.send_json({'type': 'registro_toggle_ack', **result})
        await self.channel_layer.group_send(self.group_name, {'type': 'painel.refresh'})

    @database_sync_to_async
    def _toggle_registro(self, aberto):
        # import local — mesmo motivo do import em _build_dados_painel.
        from sapl.painel.views import VoteError, _toggle_registro
        try:
            return _toggle_registro(self.scope['user'], self.sessao_id, aberto)
        except VoteError as e:
            raise Exception(e.message) from None

    @database_sync_to_async
    def _cast_vote(self, parlamentar_id, voto):
        # import local — mesmo motivo do import em _build_dados_painel.
        from sapl.painel.views import VoteError, _cast_vote
        client = self.scope.get('client') or (None, None)
        try:
            return _cast_vote(
                self.scope['user'], self.sessao_id, parlamentar_id, voto,
                ip=client[0])
        except VoteError as e:
            raise Exception(e.message) from None

    @database_sync_to_async
    def _build_dados_painel(self, sessao_id):
        # import local para evitar ciclo de import no carregamento do ASGI
        # (sapl.painel.views importa vários modelos/decorators de request
        # HTTP que não precisam existir antes do Django estar totalmente
        # pronto, o que já é garantido aqui por database_sync_to_async
        # rodar depois de django.setup() em sapl/asgi.py).
        from sapl.painel.views import build_dados_painel
        return build_dados_painel(
            _ScopeRequest(self.scope), sessao_id,
            force_mostrar_voto=getattr(self, 'is_operator', False))

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
    def _is_operator(self, user):
        """
        Papel "operador/Mesa" pra fins de mascaramento de voto (ver
        build_dados_painel(force_mostrar_voto=...)) — mais amplo que
        can_cast_vote de propósito: cobre tanto quem registra o voto
        nominal quanto quem só opera o painel (abre/fecha, cronômetro),
        que também não deveria ficar sujeito à máscara pensada pro
        público.
        """
        return user.has_module_perms(PainelAppConfig.label) or \
            user.has_module_perms('sessao')

    @database_sync_to_async
    def _can_cast_vote(self, user):
        # Mesmo gate de vote_controller (check_permission em
        # sapl/painel/views.py) — import local, mesmo motivo de sempre.
        from sapl.painel.views import check_permission
        return check_permission(user)

    @database_sync_to_async
    def _sessao_existe(self, sessao_id):
        return SessaoPlenaria.objects.filter(id=sessao_id).exists()
