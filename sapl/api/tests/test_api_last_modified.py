"""
Last-Modified e requisições condicionais (If-Modified-Since e
If-Unmodified-Since) nos models com data de atualização
(data_ultima_atualizacao ou ultima_edicao).

A data é calculada depois da autenticação, das permissões e do throttling do
DRF, sobre o mesmo queryset da view. Um objeto oculto, uma requisição negada
ou uma requisição inválida respondem como se a data não existisse: sem
Last-Modified, sem 304 e sem 412.
"""
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve
from django.utils import timezone
from model_bakery import baker
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework.throttling import BaseThrottle

from sapl.api.tests.conftest import ids
from sapl.base.models import DOC_ADM_OSTENSIVO, DOC_ADM_RESTRITIVO, AppConfig
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import SessaoPlenaria


pytestmark = pytest.mark.django_db

URL_MATERIA = '/api/materia/materialegislativa/'
URL_DOCUMENTO = '/api/protocoloadm/documentoadministrativo/'
URL_SESSAO = '/api/sessao/sessaoplenaria/'
PK_INEXISTENTE = 999999

ANTES = datetime(2024, 1, 2, 3, 4, 5, tzinfo=dt_timezone.utc)
DEPOIS = datetime(2024, 6, 7, 8, 9, 10, tzinfo=dt_timezone.utc)
HTTP_ANTES = 'Tue, 02 Jan 2024 03:04:05 GMT'
HTTP_DEPOIS = 'Fri, 07 Jun 2024 08:09:10 GMT'
HTTP_FUTURO = 'Fri, 01 Jan 2100 00:00:00 GMT'

CONDICIONAIS = [
    pytest.param({}, id='sem-condicional'),
    pytest.param({'HTTP_IF_MODIFIED_SINCE': HTTP_FUTURO},
                 id='if-modified-since'),
    pytest.param({'HTTP_IF_UNMODIFIED_SINCE': HTTP_FUTURO},
                 id='if-unmodified-since'),
]


def atualizado_em(obj, data):
    # data_ultima_atualizacao tem auto_now: só o update() grava outra data
    type(obj).objects.filter(pk=obj.pk).update(data_ultima_atualizacao=data)


def sessao_nao_iniciada(dias):
    """
    Sessão daqui a `dias` dias, não iniciada e sem pauta publicada. No
    futuro, o anônimo não a vê; no passado, vê.
    """
    return baker.make(
        SessaoPlenaria,
        data_inicio=timezone.localdate() + timedelta(days=dias),
        iniciada=False, publicar_pauta=False)


@pytest.fixture(params=['anonimo', 'autenticado'])
def cliente(request, api, usuario):
    if request.param == 'anonimo':
        return api()
    return api(usuario('operador'))


@pytest.mark.parametrize('url, params', [
    pytest.param(URL_MATERIA, {'tipo': 'abc'},
                 id='fk-com-valor-que-nao-e-id'),
    pytest.param(URL_SESSAO, {'correspondencias': PK_INEXISTENTE},
                 id='m2m-com-id-inexistente'),
    pytest.param('/api/norma/normajuridica/', {'data': '2020-13-45'},
                 id='data-invalida'),
])
def test_filtro_invalido_responde_400(cliente, url, params):
    response = cliente.get(url, params)

    assert response.status_code == 400
    assert set(response.json()) == set(params)
    assert not response.has_header('Last-Modified')


def test_pk_invalido_responde_404(cliente):
    response = cliente.get(f'{URL_MATERIA}abc/')

    assert response.status_code == 404
    assert not response.has_header('Last-Modified')


def test_last_modified_da_listagem_considera_os_filtros(api):
    tipo, outro_tipo = baker.make(TipoMateriaLegislativa, _quantity=2)
    atualizado_em(baker.make(MateriaLegislativa, tipo=tipo), ANTES)
    atualizado_em(baker.make(MateriaLegislativa, tipo=outro_tipo), DEPOIS)

    response = api().get(URL_MATERIA, {'tipo': tipo.pk})
    assert response.status_code == 200
    assert response['Last-Modified'] == HTTP_ANTES

    response = api().get(URL_MATERIA)
    assert response.status_code == 200
    assert response['Last-Modified'] == HTTP_DEPOIS

    response = api().get(URL_MATERIA, {'tipo': tipo.pk},
                         HTTP_IF_MODIFIED_SINCE=HTTP_ANTES)
    assert response.status_code == 304


def test_last_modified_do_detalhe(api, usuario):
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)
    documento = baker.make(DocumentoAdministrativo, restrito=True)
    atualizado_em(documento, DEPOIS)
    url = f'{URL_DOCUMENTO}{documento.pk}/'
    servidor = api(usuario('servidor'))

    response = servidor.get(url)
    assert response.status_code == 200
    assert response['Last-Modified'] == HTTP_DEPOIS

    response = servidor.get(url, HTTP_IF_MODIFIED_SINCE=HTTP_DEPOIS)
    assert response.status_code == 304

    response = servidor.get(url, HTTP_IF_UNMODIFIED_SINCE=HTTP_ANTES)
    assert response.status_code == 412


@pytest.fixture(params=['documento-restrito', 'sessao-nao-iniciada'])
def detalhes_oculto_e_inexistente(request):
    """
    URLs do detalhe de um objeto que o anônimo não vê e do detalhe de um id
    inexistente, no mesmo endpoint.
    """
    if request.param == 'documento-restrito':
        baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)
        url = URL_DOCUMENTO
        oculto = baker.make(DocumentoAdministrativo, restrito=True)
    else:
        url = URL_SESSAO
        oculto = sessao_nao_iniciada(dias=30)
    return f'{url}{oculto.pk}/', f'{url}{PK_INEXISTENTE}/'


@pytest.mark.parametrize('condicional', CONDICIONAIS)
def test_detalhe_de_objeto_oculto_responde_como_inexistente(
        api, detalhes_oculto_e_inexistente, condicional):
    for url in detalhes_oculto_e_inexistente:
        response = api().get(url, **condicional)

        assert response.status_code == 404, url
        assert not response.has_header('Last-Modified'), url


@pytest.mark.parametrize('condicional', CONDICIONAIS)
def test_listagem_negada_nao_depende_dos_filtros(api, condicional):
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_RESTRITIVO)
    baker.make(DocumentoAdministrativo, restrito=False,
               assunto='Compra de merenda')

    for termo in ('merenda', 'inexistente'):
        response = api().get(
            URL_DOCUMENTO, {'assunto__icontains': termo}, **condicional)

        assert response.status_code == 401, termo
        assert not response.has_header('Last-Modified'), termo


def test_escrita_negada_ignora_if_unmodified_since(api):
    materia = baker.make(MateriaLegislativa)

    for pk in (materia.pk, PK_INEXISTENTE):
        response = api().patch(f'{URL_MATERIA}{pk}/', {}, format='json',
                               HTTP_IF_UNMODIFIED_SINCE=HTTP_FUTURO)

        assert response.status_code == 401, pk


class NegaTudo(BaseThrottle):

    def allow_request(self, request, view):
        return False

    def wait(self):
        return 60


@pytest.mark.parametrize('condicional', CONDICIONAIS)
def test_throttling_vem_antes_do_last_modified(api, monkeypatch, condicional):
    baker.make(MateriaLegislativa)
    viewset = resolve(URL_MATERIA).func.cls
    monkeypatch.setattr(viewset, 'throttle_classes', [NegaTudo])
    tabela = MateriaLegislativa._meta.db_table

    with CaptureQueriesContext(connection) as consultas:
        response = api().get(URL_MATERIA, **condicional)

    assert response.status_code == 429
    assert not response.has_header('Last-Modified')
    assert not [q['sql'] for q in consultas.captured_queries
                if tabela in q['sql']]


def test_last_modified_de_quem_usa_token_considera_o_que_ele_ve(usuario):
    visivel = sessao_nao_iniciada(dias=-30)
    oculta = sessao_nao_iniciada(dias=30)
    atualizado_em(visivel, ANTES)
    atualizado_em(oculta, DEPOIS)

    response = APIClient().get(URL_SESSAO)
    assert ids(response) == {visivel.pk}
    assert response['Last-Modified'] == HTTP_ANTES

    # sapl.api.signals cria o token de todo usuário novo
    token = Token.objects.get(user=usuario('integracao'))
    com_token = APIClient()
    com_token.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    response = com_token.get(URL_SESSAO)
    assert ids(response) == {visivel.pk, oculta.pk}
    assert response['Last-Modified'] == HTTP_DEPOIS

    # A sessão que o anônimo não vê mudou depois de ANTES
    response = com_token.get(URL_SESSAO, HTTP_IF_MODIFIED_SINCE=HTTP_ANTES)
    assert response.status_code == 200
