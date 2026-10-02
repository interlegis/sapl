import uuid

import pytest
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from model_bakery import baker

from sapl.base.models import AppConfig as ConfiguracoesAplicacao
from sapl.painel.consumers import PainelConsumer
from sapl.parlamentares.models import Legislatura, SessaoLegislativa
from sapl.sessao.models import SessaoPlenaria, TipoSessaoPlenaria

# Layer em memória para os testes — group_send/group_add não precisam de um
# Redis de verdade rodando; isso é o padrão recomendado pelo próprio
# Channels para testes (a validação end-to-end com Redis de verdade fica
# para a verificação manual em navegador, ver Parte 3 do plano).
#
# Usado via a fixture `settings` do pytest-django (autouse abaixo) em vez
# de @override_settings como decorator: neste Django 2.2 (sem suporte
# nativo a testes async), override_settings como decorator envolve a
# função com um wrapper síncrono que faz pytest-asyncio deixar de
# reconhecer a test function como uma coroutine — os testes eram
# silenciosamente pulados (PytestUnhandledCoroutineWarning) em vez de
# rodar.
IN_MEMORY_LAYER = {
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
}


@pytest.fixture(autouse=True)
def in_memory_channel_layer(settings):
    settings.CHANNEL_LAYERS = IN_MEMORY_LAYER


@sync_to_async
def _make_sessao():
    baker.make(ConfiguracoesAplicacao, mostrar_voto=True, mostrar_brasao_painel=False)
    legislatura = baker.make(Legislatura)
    sessao_legislativa = baker.make(SessaoLegislativa)
    tipo = baker.make(TipoSessaoPlenaria)
    return baker.make(SessaoPlenaria, legislatura=legislatura,
                      sessao_legislativa=sessao_legislativa, tipo=tipo, numero=1)


@sync_to_async
def _make_user(module_perms=None):
    user = get_user_model().objects.create_user(
        username='ws-user-{}'.format(uuid.uuid4().hex[:12]), password='x')
    if module_perms:
        user.user_permissions.add(
            *Permission.objects.filter(content_type__app_label=module_perms))
    return user


async def _communicator(sessao_id, user, session=None):
    communicator = WebsocketCommunicator(
        PainelConsumer.as_asgi(), '/ws/painel/{}/'.format(sessao_id))
    communicator.scope['user'] = user
    communicator.scope['session'] = session if session is not None else {}
    communicator.scope['url_route'] = {'kwargs': {'sessao_id': sessao_id}}
    return communicator


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_connect_autenticado_e_permitido_recebe_payload_inicial():
    sessao = await _make_sessao()
    user = await _make_user(module_perms='painel')

    communicator = await _communicator(sessao.pk, user)
    connected, _subprotocol = await communicator.connect()
    assert connected

    primeira_mensagem = await communicator.receive_json_from()
    assert primeira_mensagem['type'] == 'data'
    assert 'sessao_plenaria' in primeira_mensagem['payload']

    await communicator.disconnect()


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_connect_nao_autenticado_e_rejeitado():
    sessao = await _make_sessao()

    communicator = await _communicator(sessao.pk, AnonymousUser())
    connected, close_code = await communicator.connect()

    assert not connected
    assert close_code == 4401


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_connect_autenticado_sem_nenhuma_permissao_e_rejeitado():
    sessao = await _make_sessao()
    user = await _make_user(module_perms=None)

    communicator = await _communicator(sessao.pk, user)
    connected, close_code = await communicator.connect()

    assert not connected
    assert close_code == 4403


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_connect_sessao_inexistente_e_rejeitado_sem_excecao_nao_tratada():
    user = await _make_user(module_perms='painel')

    communicator = await _communicator(999999, user)
    connected, close_code = await communicator.connect()

    assert not connected
    assert close_code == 4404


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_broadcast_no_grupo_da_sessao_e_recebido_pelo_cliente_conectado():
    sessao = await _make_sessao()
    user = await _make_user(module_perms='painel')

    communicator = await _communicator(sessao.pk, user)
    connected, _subprotocol = await communicator.connect()
    assert connected
    await communicator.receive_json_from()  # payload inicial, descarta

    layer = get_channel_layer()
    await layer.group_send('sessao_{}'.format(sessao.pk),
                           {'type': 'data', 'payload': {'foo': 'bar'}})

    mensagem = await communicator.receive_json_from()
    assert mensagem == {'type': 'data', 'payload': {'foo': 'bar'}}

    await communicator.disconnect()


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_ping_recebe_pong():
    sessao = await _make_sessao()
    user = await _make_user(module_perms='painel')

    communicator = await _communicator(sessao.pk, user)
    connected, _subprotocol = await communicator.connect()
    assert connected
    await communicator.receive_json_from()  # payload inicial, descarta

    await communicator.send_json_to({'type': 'ping'})
    resposta = await communicator.receive_json_from()
    assert resposta == {'type': 'pong'}

    await communicator.disconnect()
