"""
Prova que as views que alteram voto/matéria (Parte 3 do plano) realmente
disparam um broadcast que chega no grupo WebSocket certo — complementa
test_consumers.py (que testa o consumer isolado) e os testes em
sapl/painel/tests/tests.py que já confirmam a chamada não quebra a view
quando o layer não está disponível (Redis fora do ar).
"""
from datetime import timedelta

import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from sapl.base.models import AppConfig as ConfiguracoesAplicacao
from sapl.painel.consumers import PainelConsumer
from sapl.painel.tests.tests import (NOMINAL, _materia, _ordem_nominal_aberta,
                                     _presente_com_mandato,
                                     _votante_com_client)
from sapl.parlamentares.models import Mandato, Parlamentar
from sapl.sessao.models import Orador, OrdemDia, PresencaOrdemDia, TipoResultadoVotacao

IN_MEMORY_LAYER = {
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
}


@pytest.fixture(autouse=True)
def in_memory_channel_layer(settings):
    settings.CHANNEL_LAYERS = IN_MEMORY_LAYER


@pytest.fixture(autouse=True)
def locmem_cache(settings):
    # cronômetro (último trigger point) vive no cache padrão do projeto,
    # que é file-based e persiste em disco entre runs — isola aqui do
    # mesmo jeito que o layer acima isola o Redis real.
    settings.CACHES = {
        'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    }


@sync_to_async
def _setup_ordem_aberta():
    baker.make(ConfiguracoesAplicacao, mostrar_voto=True, mostrar_brasao_painel=False)
    return _ordem_nominal_aberta()


@sync_to_async
def _votante(sessao):
    parlamentar, client = _votante_com_client(sessao)
    # get_presentes() (Parte 1) só inclui quem tem Mandato pra legislatura
    # da sessão — _votante_com_client() não cria um, então sem isso o
    # parlamentar nunca apareceria em `presentes`, com ou sem WebSockets.
    baker.make(Mandato, parlamentar=parlamentar, legislatura=sessao.legislatura,
               data_inicio_mandato=sessao.data_inicio)
    return parlamentar, client


@sync_to_async
def _admin_client_login():
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('admin-ws', 'admin@x.com', 'x')
    client = Client()
    client.force_login(user)
    return client, user


async def _painel_communicator(sessao_id, admin_user):
    communicator = WebsocketCommunicator(
        PainelConsumer.as_asgi(), '/ws/painel/{}/'.format(sessao_id))
    communicator.scope['user'] = admin_user
    communicator.scope['session'] = {}
    communicator.scope['url_route'] = {'kwargs': {'sessao_id': sessao_id}}
    connected, _sub = await communicator.connect()
    assert connected
    await communicator.receive_json_from()  # payload inicial, descarta
    return communicator


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_voto_do_tablet_dispara_broadcast_com_voto_atualizado():
    # Limpeza explícita no final, em vez de confiar no rollback atômico do
    # pytest-django: channels.db.database_sync_to_async despacha pro
    # worker thread "thread sensitive" do asgiref, que pega sua própria
    # conexão nova com o banco (autocommit) — fora da savepoint que o
    # fixture `django_db` abriu na thread principal. Sem isso, cada teste
    # aqui commitaria de verdade uma OrdemDia com votacao_aberta=True que
    # nunca seria desfeita, quebrando a constraint única pro próximo teste
    # (confirmado: aconteceu, a fileira ficava só na base de testes,
    # invisível numa conexão nova, mas viva pro resto da run do pytest).
    sessao, ordem = await _setup_ordem_aberta()
    try:
        admin_client, admin_user = await _admin_client_login()
        parlamentar, votante_client = await _votante(sessao)

        communicator = await _painel_communicator(sessao.pk, admin_user)

        await sync_to_async(votante_client.post)(
            reverse('sapl.painel:voto_individual'), {'voto': 'Sim'})

        mensagem = await communicator.receive_json_from()
        assert mensagem['type'] == 'data'
        votos = {p['parlamentar_id']: p['voto'] for p in mensagem['payload']['presentes']}
        assert votos[parlamentar.pk] == 'Sim'

        await communicator.disconnect()
    finally:
        await sync_to_async(sessao.delete)()


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_encerrar_votacao_dispara_broadcast():
    """
    Registro individual de votação nominal (o "salvar-votacao" em lote da
    tela legada nominal.html não existe mais — ver plano de unificação
    Expediente/OrdemDia) agora é: um voto por chamada a vote_controller
    (o mesmo caminho HTTP que PainelConsumer usa por baixo pro type:
    "vote" — vote_controller continua existindo por compatibilidade),
    seguido de close_voting pra fechar e apurar o resultado.
    """
    sessao, ordem = await _setup_ordem_aberta()
    try:
        admin_client, admin_user = await _admin_client_login()
        parlamentar, votante_client = await _votante(sessao)
        tipo_resultado = await sync_to_async(baker.make)(
            TipoResultadoVotacao, nome='Aprovada', natureza='A')

        communicator = await _painel_communicator(sessao.pk, admin_user)

        await sync_to_async(admin_client.post)(
            reverse('sapl.painel:vote_controller', kwargs={'controller_id': sessao.pk}),
            {'parlamentar_id': parlamentar.pk, 'voto': 'Sim'})
        # Descarta o refresh disparado pelo voto — este teste verifica o
        # broadcast do close_voting especificamente.
        await communicator.receive_json_from()

        await sync_to_async(admin_client.post)(
            reverse('sapl.painel:close_voting', kwargs={'controller_id': sessao.pk}),
            {'resultado_id': tipo_resultado.pk, 'observacoes': ''})

        mensagem = await communicator.receive_json_from()
        assert mensagem['type'] == 'data'
        assert mensagem['payload']['numero_votos_sim'] == 1
        assert mensagem['payload']['registro'] is True

        await communicator.disconnect()
    finally:
        await sync_to_async(sessao.delete)()


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_abrir_votacao_dispara_broadcast():
    sessao, ordem_antiga = await _setup_ordem_aberta()
    try:
        admin_client, admin_user = await _admin_client_login()

        def _prepara():
            ordem_antiga.votacao_aberta = False
            ordem_antiga.save()
            sessao.iniciada = True
            sessao.finalizada = False
            sessao.save()
            baker.make(PresencaOrdemDia, sessao_plenaria=sessao,
                       parlamentar=baker.make(Parlamentar, ativo=True))
            return baker.make(OrdemDia, sessao_plenaria=sessao, materia=_materia(),
                              tipo_votacao=NOMINAL, votacao_aberta=False)
        nova_ordem = await sync_to_async(_prepara)()

        communicator = await _painel_communicator(sessao.pk, admin_user)

        url = reverse('sapl.sessao:abrir_votacao', kwargs={'pk': nova_ordem.pk, 'spk': sessao.pk})
        url += '?tipo_materia=ordem'
        await sync_to_async(admin_client.get)(url)

        mensagem = await communicator.receive_json_from()
        assert mensagem['type'] == 'data'

        await communicator.disconnect()
    finally:
        await sync_to_async(sessao.delete)()


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_cronometro_dispara_broadcast_com_valor_atualizado():
    sessao, ordem = await _setup_ordem_aberta()
    try:
        def _abre_painel():
            sessao.painel_aberto = True
            sessao.save()
        await sync_to_async(_abre_painel)()

        admin_client, admin_user = await _admin_client_login()
        communicator = await _painel_communicator(sessao.pk, admin_user)

        await sync_to_async(admin_client.get)(
            reverse('sapl.painel:cronometro_painel'),
            {'tipo': 'discurso', 'action': 'start'})

        mensagem = await communicator.receive_json_from()
        assert mensagem['type'] == 'data'
        assert mensagem['payload']['cronometro_discurso'] == 'start'

        await communicator.disconnect()
    finally:
        await sync_to_async(sessao.delete)()


@pytest.mark.django_db(transaction=False)
@pytest.mark.asyncio
async def test_criar_e_apagar_orador_disparam_broadcast():
    """
    BroadcastPainelOnSaveMixin (sapl/sessao/views.py) — sem isso, oradores
    só chegavam ao painel no próximo poll (agora removido). Cobre tanto
    form_valid() (create) quanto delete(), incluindo o caso em que
    self.kwargs['pk'] em DeleteView é o pk do próprio Orador, não o da
    SessaoPlenaria (por isso o mixin lê self.object.sessao_plenaria_id em
    vez de kwargs — ver a docstring do mixin).
    """
    sessao, ordem = await _setup_ordem_aberta()
    try:
        admin_client, admin_user = await _admin_client_login()

        def _prepara():
            return _presente_com_mandato(
                sessao,
                data_inicio_mandato=sessao.data_inicio - timedelta(days=365),
                data_fim_mandato=sessao.data_inicio + timedelta(days=365))
        parlamentar = await sync_to_async(_prepara)()

        communicator = await _painel_communicator(sessao.pk, admin_user)

        create_url = reverse('sapl.sessao:orador_create', kwargs={'pk': sessao.pk})
        response = await sync_to_async(admin_client.post)(create_url, {
            'parlamentar': str(parlamentar.pk),
            'numero_ordem': '1',
        })
        assert response.status_code == 302

        mensagem = await communicator.receive_json_from()
        assert mensagem['type'] == 'data'

        orador = await sync_to_async(
            lambda: Orador.objects.get(sessao_plenaria=sessao, parlamentar=parlamentar)
        )()

        delete_url = reverse('sapl.sessao:orador_delete', kwargs={'pk': orador.pk})
        response = await sync_to_async(admin_client.post)(delete_url)
        assert response.status_code == 302

        mensagem = await communicator.receive_json_from()
        assert mensagem['type'] == 'data'

        await communicator.disconnect()
    finally:
        await sync_to_async(sessao.delete)()
