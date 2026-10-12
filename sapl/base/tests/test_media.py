from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.http import Http404
from django.utils import timezone
from model_bakery import baker
import pytest

from sapl.base.media import media
from sapl.base.models import AppConfig, Autor
from sapl.materia.models import Proposicao
from sapl.protocoloadm.models import (DocumentoAcessorioAdministrativo,
                                      DocumentoAdministrativo)

DOC_PATH = 'sapl/private/documentoadministrativo/2026/1/texto.pdf'
ACESSORIO_PATH = 'sapl/public/documentoacessorioadministrativo/2026/1/a.pdf'
PROPOSICAO_PATH = 'sapl/private/proposicao/2026/1/proposicao.pdf'


@pytest.fixture(autouse=True)
def limpa_cache_appconfig():
    # o cache em arquivo sobrevive ao rollback do teste
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def sem_debug(settings):
    settings.DEBUG = False


def _config(comportamento):
    cache.clear()
    AppConfig.objects.all().delete()
    baker.make(AppConfig, documentos_administrativos=comportamento)


def _login(client, username, perm=None):
    user = baker.make(get_user_model(), username=username)
    if perm:
        app_label, codename = perm.split('.')
        perm_obj = Permission.objects.filter(
            content_type__app_label=app_label, codename=codename).first()
        if not perm_obj:
            perm_obj = Permission.objects.create(
                codename=codename, name=codename,
                content_type=ContentType.objects.get_for_model(
                    DocumentoAdministrativo))
        user.user_permissions.add(perm_obj)
    client.force_login(user)
    return user


def _get(client, path):
    return client.get('/media/' + path)


def _assert_servido(response, path):
    assert response.status_code == 200
    assert response['X-Accel-Redirect'] == '/media-interna/' + path
    assert response['X-Content-Type-Options'] == 'nosniff'
    assert response['Cache-Control'] == 'private'


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('comportamento,restrito,perfil,pode_ver', [
    ('O', False, None, True),
    ('O', True, None, False),
    ('O', True, 'logado', True),
    ('R', False, None, False),
    ('R', False, 'logado', False),
    ('R', True, 'com_permissao', True),
])
def test_documento_administrativo(client, comportamento, restrito, perfil,
                                  pode_ver):
    _config(comportamento)
    baker.make(DocumentoAdministrativo, restrito=restrito,
               texto_integral=DOC_PATH)
    if perfil == 'logado':
        _login(client, 'logado')
    elif perfil == 'com_permissao':
        _login(client, 'perm',
               'protocoloadm.detail_documentoadministrativo')

    response = _get(client, DOC_PATH)

    if pode_ver:
        _assert_servido(response, DOC_PATH)
        assert response['Content-Type'] == 'application/pdf'
    else:
        assert response.status_code == 404
        assert not response.has_header('X-Accel-Redirect')


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('restrito,pode_ver', [(False, True), (True, False)])
def test_documento_acessorio_segue_documento(client, restrito, pode_ver):
    _config('O')
    documento = baker.make(DocumentoAdministrativo, restrito=restrito)
    baker.make(DocumentoAcessorioAdministrativo, documento=documento,
               arquivo=ACESSORIO_PATH)

    response = _get(client, ACESSORIO_PATH)

    assert response.status_code == (200 if pode_ver else 404)


@pytest.mark.django_db(transaction=False)
def test_caminho_legado_e_prefixo_ponto_barra(client):
    _config('O')
    legado = 'sapl/public/documentoadministrativo/2010/7/antigo.pdf'
    baker.make(DocumentoAdministrativo, texto_integral=legado)
    baker.make(DocumentoAdministrativo, texto_integral='./' + DOC_PATH)

    _assert_servido(_get(client, legado), legado)
    _assert_servido(_get(client, DOC_PATH), DOC_PATH)


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('path', [
    'sapl/private/documentoadministrativo/2026/1/inexistente.pdf',
    'sapl/private/outromodelo/2026/1/texto.pdf',
    'sapl/private/documentoadministrativo/../../public/x.pdf',
    'sapl/private/documentoadministrativo/%2e%2e/x.pdf',
])
def test_caminho_invalido(client, path):
    _config('O')
    baker.make(DocumentoAdministrativo, texto_integral=DOC_PATH)

    assert _get(client, path).status_code == 404


@pytest.mark.django_db(transaction=False)
def test_extensao_ativa_e_baixada(client):
    _config('O')
    path = 'sapl/private/documentoadministrativo/2026/1/x.html'
    baker.make(DocumentoAdministrativo, texto_integral=path)

    response = _get(client, path)

    _assert_servido(response, path)
    assert response['Content-Type'] == 'application/octet-stream'
    assert response['Content-Disposition'].startswith('attachment;')


@pytest.mark.django_db(transaction=False)
def test_nome_nao_ascii_codificado(client):
    _config('O')
    path = 'sapl/private/documentoadministrativo/2026/1/ofício_nº1.pdf'
    baker.make(DocumentoAdministrativo, texto_integral=path)

    response = _get(client, path)

    assert response.status_code == 200
    assert response['X-Accel-Redirect'] == (
        '/media-interna/sapl/private/documentoadministrativo/2026/1/'
        'of%C3%ADcio_n%C2%BA1.pdf')


def _proposicao(enviada=False, recebida=False):
    autor = baker.make(Autor)
    operador = baker.make(get_user_model(), username='operador')
    autor.operadores.add(operador)
    agora = timezone.now()
    baker.make(Proposicao, autor=autor, texto_original=PROPOSICAO_PATH,
               data_envio=agora if enviada or recebida else None,
               data_recebimento=agora if recebida else None)
    return operador


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('estado,perfil,pode_ver', [
    ('rascunho', 'operador', True),
    ('rascunho', 'outro', False),
    ('rascunho', 'protocolo', False),
    ('rascunho', None, False),
    ('enviada', 'protocolo', True),
    ('enviada', 'outro', False),
    ('enviada', None, False),
    ('recebida', None, True),
])
def test_proposicao(client, estado, perfil, pode_ver):
    operador = _proposicao(enviada=estado == 'enviada',
                           recebida=estado == 'recebida')
    if perfil == 'operador':
        client.force_login(operador)
    elif perfil == 'outro':
        _login(client, 'outro')
    elif perfil == 'protocolo':
        _login(client, 'protocolo',
               'protocoloadm.detail_documentoadministrativo')

    response = _get(client, PROPOSICAO_PATH)

    assert response.status_code == (200 if pode_ver else 404)


@pytest.mark.django_db(transaction=False)
def test_arquivo_publico_passa_por_x_accel(client):
    path = 'sapl/public/materialegislativa/2026/1/materia.pdf'

    response = _get(client, path)

    assert response.status_code == 200
    assert response['X-Accel-Redirect'] == '/media-interna/' + path
    assert response['Content-Type'] == 'application/pdf'
    assert response['X-Content-Type-Options'] == 'nosniff'
    assert not response.has_header('Cache-Control')


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('nome', ['x.svg', 'x.html', 'x.XML', 'x.js'])
def test_arquivo_publico_ativo_e_baixado(client, nome):
    response = _get(client, 'sapl/public/normajuridica/2026/1/' + nome)

    assert response['Content-Type'] == 'application/octet-stream'
    assert response['Content-Disposition'].startswith('attachment;')


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('path', [
    'sapl/public/../private/documentoadministrativo/2026/1/texto.pdf',
    'sapl//private/documentoadministrativo/2026/1/texto.pdf',
    'sapl/./private/documentoadministrativo/2026/1/texto.pdf',
    'sapl/public/normajuridica/',
])
def test_caminho_nao_normalizado(client, path):
    assert _get(client, path).status_code == 404


@pytest.mark.django_db(transaction=False)
def test_debug_serve_arquivo(rf, settings, tmp_path):
    settings.DEBUG = True
    settings.MEDIA_ROOT = str(tmp_path)
    _config('R')
    publico = tmp_path / 'sapl/public/normajuridica/1/n.pdf'
    publico.parent.mkdir(parents=True)
    publico.write_bytes(b'%PDF-1.4 norma')
    baker.make(DocumentoAdministrativo, texto_integral=DOC_PATH)

    def chama(path):
        request = rf.get('/media/' + path)
        request.user = AnonymousUser()
        return media(request, path)

    response = chama('sapl/public/normajuridica/1/n.pdf')
    assert b''.join(response.streaming_content) == b'%PDF-1.4 norma'
    assert not response.has_header('X-Accel-Redirect')

    for path in (DOC_PATH, 'sapl/public/normajuridica/1/nao.pdf'):
        with pytest.raises(Http404):
            chama(path)
