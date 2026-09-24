import datetime

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from sapl.base.models import AppConfig as ConfiguracoesAplicacao
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.painel.views import build_dados_painel
from sapl.parlamentares.models import (Filiacao, Legislatura, Mandato,
                                       Parlamentar, Partido,
                                       SessaoLegislativa, Votante)
from sapl.sessao.models import (OrdemDia, PresencaOrdemDia, SessaoPlenaria,
                                TipoResultadoVotacao, TipoSessaoPlenaria,
                                VotoParlamentar)

NOMINAL = 2


def _sessao_plenaria(data_inicio=None):
    legislatura = baker.make(Legislatura)
    sessao_legislativa = baker.make(SessaoLegislativa)
    tipo = baker.make(TipoSessaoPlenaria)
    kwargs = {}
    if data_inicio is not None:
        kwargs['data_inicio'] = data_inicio
    return baker.make(SessaoPlenaria, legislatura=legislatura,
                      sessao_legislativa=sessao_legislativa, tipo=tipo, numero=1,
                      **kwargs)


def _presente_com_mandato(sessao, data_inicio_mandato, data_fim_mandato=None,
                          partido_sigla=None, filiacao_data=None):
    """
    Como _presente() (que ainda não existia neste arquivo antes desta
    regressão), mas cria também um Mandato — nenhuma fixture deste arquivo
    fazia isso antes, então nenhum teste aqui de fato exercia o ramo de
    get_presentes() que confere `mandato_set.filter(legislatura=...)`. É
    exatamente esse ramo que Milestone 1 troca por uma view SQL, então
    precisa de cobertura própria antes de qualquer refatoração.
    """
    parlamentar = baker.make(Parlamentar, ativo=True)
    baker.make(PresencaOrdemDia, sessao_plenaria=sessao, parlamentar=parlamentar)
    baker.make(Mandato, parlamentar=parlamentar, legislatura=sessao.legislatura,
               data_inicio_mandato=data_inicio_mandato,
               data_fim_mandato=data_fim_mandato)
    if partido_sigla:
        partido = baker.make(Partido, sigla=partido_sigla)
        baker.make(Filiacao, parlamentar=parlamentar, partido=partido,
                   data=filiacao_data or data_inicio_mandato)
    return parlamentar


def _materia():
    tipo_materia = baker.make(TipoMateriaLegislativa)
    return baker.make(MateriaLegislativa, tipo=tipo_materia)


def _ordem_nominal_aberta(registro_aberto=False):
    sessao = _sessao_plenaria()
    materia = _materia()
    ordem = baker.make(OrdemDia, sessao_plenaria=sessao, materia=materia,
                       tipo_votacao=NOMINAL, votacao_aberta=True,
                       registro_aberto=registro_aberto)
    return sessao, ordem


def _votante(sessao, admin_user):
    parlamentar = baker.make(Parlamentar, ativo=True)
    baker.make(PresencaOrdemDia, sessao_plenaria=sessao, parlamentar=parlamentar)
    baker.make(Votante, parlamentar=parlamentar, user=admin_user)
    return parlamentar


def _votante_com_client(sessao):
    """
    Como _votante(), mas cria seu próprio usuário (não-superuser, só com a
    permissão parlamentares.can_vote) e devolve um Client logado separado —
    necessário para testar a corrida entre o operador e o vereador, que
    precisam ser duas sessões/usuários distintos.
    """
    parlamentar = baker.make(Parlamentar, ativo=True)
    baker.make(PresencaOrdemDia, sessao_plenaria=sessao, parlamentar=parlamentar)
    user = get_user_model().objects.create_user(
        username='votante-{}'.format(parlamentar.pk), password='x')
    user.user_permissions.add(Permission.objects.get(codename='can_vote'))
    baker.make(Votante, parlamentar=parlamentar, user=user)
    client = Client()
    client.force_login(user)
    return parlamentar, client


@pytest.mark.django_db(transaction=False)
def test_votante_view_envia_headers_never_cache(admin_client, admin_user):
    sessao, ordem = _ordem_nominal_aberta()
    _votante(sessao, admin_user)

    response = admin_client.get(reverse('sapl.painel:voto_individual'))

    assert response.status_code == 200
    assert 'no-store' in response['Cache-Control']


@pytest.mark.django_db(transaction=False)
def test_votante_view_mostra_materia_quando_registro_fechado(admin_client, admin_user):
    sessao, ordem = _ordem_nominal_aberta(registro_aberto=False)
    _votante(sessao, admin_user)

    response = admin_client.get(reverse('sapl.painel:voto_individual'))

    assert response.status_code == 200
    assert 'error_message' not in response.context
    assert response.context['materia'] == ordem.materia


@pytest.mark.django_db(transaction=False)
def test_votante_view_mostra_erro_explicito_quando_registro_bloqueado(admin_client, admin_user):
    """
    Regressão da causa raiz #1: quando a Mesa bloqueia novos votos
    (registro_aberto=True), o vereador que ainda não votou precisa ver uma
    mensagem explícita — não uma tela em branco sem explicação.
    """
    sessao, ordem = _ordem_nominal_aberta(registro_aberto=True)
    _votante(sessao, admin_user)

    response = admin_client.get(reverse('sapl.painel:voto_individual'))

    assert response.status_code == 200
    assert 'Mesa encerrou o recebimento de novos votos' in response.context['error_message']


@pytest.mark.django_db(transaction=False)
def test_voto_do_vereador_prevalece_sobre_lote_do_operador(admin_client):
    """
    Invariante: o voto do próprio vereador sempre prevalece sobre qualquer
    valor provisório já existente para ele (ex.: de uma tentativa anterior
    do operador, ou de qualquer outra origem). Complementa
    test_salvar_votacao_nao_sobrescreve_voto_ja_registrado (que cobre a
    ordem inversa: o operador não pode sobrescrever um voto real já
    registrado) — aqui é o vereador votando por cima de um valor existente
    através da view de verdade, não apenas o estado inicial simulado.
    """
    sessao, ordem = _ordem_nominal_aberta()
    vereador, votante_client = _votante_com_client(sessao)

    # 1) Já existe um valor provisório "Não Votou" para o vereador (ex.: o
    #    <select> nunca foi tocado pelo operador). Esse valor nunca deveria
    #    impedir o vereador de votar de verdade.
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=vereador,
               voto='Não Votou')

    # 2) O vereador vota pelo tablet — seu voto real prevalece sobre o
    #    valor provisório.
    response = votante_client.post(
        reverse('sapl.painel:voto_individual'), {'voto': 'Sim'})
    assert response.status_code == 302

    voto = VotoParlamentar.objects.get(ordem=ordem, parlamentar=vereador)
    assert voto.voto == 'Sim'


@pytest.mark.django_db(transaction=False)
def test_propria_tela_nao_mostra_voto_de_outra_materia(admin_client):
    """
    Regressão: votacao() buscava o voto do próprio vereador com
    Q(ordem=ordem_dia) | Q(expediente=expediente) — quando a matéria atual
    é uma OrdemDia, expediente é None, e Q(expediente=None) vira
    "expediente_id IS NULL" no SQL, que é verdadeiro para QUALQUER voto de
    ordem do dia daquele vereador, não só o desta matéria (idem para
    ExpedienteMateria, cujas votações também têm ordem=None). Com .first()
    sem ordenação, o vereador podia ver o voto de uma matéria antiga em vez
    do voto (ou ausência de voto) da matéria atual — inclusive depois de
    trocar o próprio voto, já que a query buscava a linha errada.
    """
    sessao, ordem_antiga = _ordem_nominal_aberta()
    vereador, votante_client = _votante_com_client(sessao)
    baker.make(VotoParlamentar, ordem=ordem_antiga, parlamentar=vereador, voto='Sim')

    ordem_antiga.votacao_aberta = False
    ordem_antiga.save()
    baker.make(OrdemDia, sessao_plenaria=sessao, materia=_materia(),
               tipo_votacao=NOMINAL, votacao_aberta=True, registro_aberto=False)
    baker.make(PresencaOrdemDia, sessao_plenaria=sessao, parlamentar=vereador)

    status_url = reverse('sapl.painel:voto_individual_status')

    # Ainda não votou na matéria atual — não pode herdar o 'Sim' da antiga.
    assert votante_client.get(status_url).json()['voto_parlamentar'] is None

    votante_client.post(reverse('sapl.painel:voto_individual'), {'voto': 'Não'})

    assert votante_client.get(status_url).json()['voto_parlamentar'] == 'Não'
    assert VotoParlamentar.objects.get(
        ordem=ordem_antiga, parlamentar=vereador).voto == 'Sim'


@pytest.fixture
def locmem_cache(settings):
    """
    O cache padrão do projeto é file-based (persiste em disco entre runs de
    teste) — cronômetro agora vive nesse cache, então sem isolar aqui os
    testes abaixo vazariam estado real pro cache de dev compartilhado.
    """
    settings.CACHES = {
        'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    }


@pytest.mark.django_db(transaction=False)
def test_cronometro_e_compartilhado_entre_sessoes_diferentes(locmem_cache, admin_client):
    """
    Regressão: get_cronometro_status() lia de request.session — o
    Presidente apertando "iniciar" no cronômetro só mudava o que ELE via;
    o telão público (outra sessão/browser) nunca via a mudança. Agora o
    estado fica em cache compartilhado, então uma segunda sessão/cliente
    completamente separada precisa ver o mesmo valor.

    Lê o resultado via build_dados_painel() diretamente (não mais pelo
    endpoint HTTP get_dados_painel/dados_painel, removido com o polling —
    ninguém mais o chama por HTTP; o mesmo build_dados_painel() é o que os
    broadcasts via WebSocket usam, então continua sendo o ponto de
    verdade certo pra este teste). request=None é seguro aqui:
    build_dados_painel() nunca lê nada de request, só repassa adiante para
    get_cronometro_status(), que também o ignora e lê do cache direto.
    """
    sessao = _sessao_plenaria()
    baker.make(ConfiguracoesAplicacao, mostrar_voto=True, mostrar_brasao_painel=False)

    admin_client.get(reverse('sapl.painel:cronometro_painel'),
                     {'tipo': 'discurso', 'action': 'start'})

    data = build_dados_painel(None, sessao.pk)
    assert data['cronometro_discurso'] == 'start'


@pytest.mark.django_db(transaction=False)
def test_votante_status_reflete_estado_e_nao_exige_permissao_do_painel():
    """
    votante_status precisa ser alcançável por uma conta só-Votante (sem
    nenhuma permissão do app painel) — é por isso que tem sua própria
    checagem de permissão (parlamentares.can_vote) em vez de reaproveitar
    check_permission (permissão de módulo do app painel).
    """
    sessao, ordem = _ordem_nominal_aberta()
    vereador, votante_client = _votante_com_client(sessao)

    status_url = reverse('sapl.painel:voto_individual_status')

    resposta = votante_client.get(status_url)
    assert resposta.status_code == 200
    data = resposta.json()
    assert data['materia_id'] == ordem.materia_id
    assert data['status_message'] == 'Aguardando seu voto.'
    assert data['voto_parlamentar'] is None

    votante_client.post(reverse('sapl.painel:voto_individual'), {'voto': 'Não'})

    resposta2 = votante_client.get(status_url)
    data2 = resposta2.json()
    assert data2['voto_parlamentar'] == 'Não'
    assert 'encerramento da votação' in data2['status_message']
