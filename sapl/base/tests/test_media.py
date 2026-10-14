import os
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.http import Http404
from django.utils import timezone
from model_bakery import baker
import pytest

from sapl.base.media import MODELOS_DE_SESSAO, RESOLVEDORES, media
from sapl.base.models import AppConfig, Autor
from sapl.materia.models import Proposicao
from sapl.protocoloadm.models import (DocumentoAcessorioAdministrativo,
                                      DocumentoAdministrativo)
from sapl.utils import EXTENSOES_ATIVAS

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


def _login(client, username, *perms):
    user = baker.make(get_user_model(), username=username)
    for perm in perms:
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
    ('R', True, None, False),
    ('R', True, 'logado', False),
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


ESTADOS_PROPOSICAO = ('rascunho', 'enviada', 'devolvida', 'incorporada')
PERMS_DOCADM = ['protocoloadm.add_documentoadministrativo',
                'protocoloadm.change_documentoadministrativo',
                'protocoloadm.detail_documentoadministrativo']


def _proposicao(estado):
    autor = baker.make(Autor)
    operador = baker.make(get_user_model(), username='operador')
    autor.operadores.add(operador)
    agora = timezone.now()
    # mesmos campos gravados pelo envio, devolução e incorporação
    baker.make(Proposicao, autor=autor, texto_original=PROPOSICAO_PATH,
               data_envio=agora if estado in ('enviada', 'incorporada')
               else None,
               data_recebimento=agora if estado == 'incorporada' else None,
               data_devolucao=agora if estado == 'devolvida' else None)
    return operador


def _login_proposicao(client, perfil, operador):
    if perfil == 'operador':
        client.force_login(operador)
    elif perfil == 'docadm':
        user = _login(client, 'docadm', *PERMS_DOCADM)
        assert user.has_module_perms('protocoloadm')
    elif perfil == 'outro':
        _login(client, 'outro')
    elif perfil:
        _login(client, perfil, 'materia.detail_proposicao_' + perfil)


def _pode_ver_proposicao(estado, perfil):
    return perfil == 'operador' or perfil == estado != 'rascunho'


GRADE_PROPOSICAO = [
    (estado, perfil, _pode_ver_proposicao(estado, perfil))
    for estado in ESTADOS_PROPOSICAO
    for perfil in (None, 'operador', 'outro', 'docadm', 'enviada',
                   'devolvida', 'incorporada')]


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('estado,perfil,pode_ver', GRADE_PROPOSICAO)
def test_proposicao(client, estado, perfil, pode_ver):
    _login_proposicao(client, perfil, _proposicao(estado))

    response = _get(client, PROPOSICAO_PATH)

    if pode_ver:
        _assert_servido(response, PROPOSICAO_PATH)
    else:
        assert response.status_code == 404


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
@pytest.mark.parametrize('nome', ['x.svg', 'x.html', 'x.XML', 'x.js',
                                  'x.xht', 'x.rdf', 'x.xslt', 'x.kml'])
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


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('debug', [False, True])
def test_link_simbolico_para_fora_de_media(rf, settings, tmp_path, debug):
    settings.DEBUG = debug
    media_root = tmp_path / 'media'
    fora = tmp_path / 'fora'
    (media_root / 'sapl/public').mkdir(parents=True)
    fora.mkdir()
    (fora / 'segredo.txt').write_bytes(b'segredo')
    (media_root / 'sapl/public/link').symlink_to(fora)
    settings.MEDIA_ROOT = str(media_root)
    request = rf.get('/media/sapl/public/link/segredo.txt')
    request.user = AnonymousUser()

    with pytest.raises(Http404):
        media(request, 'sapl/public/link/segredo.txt')


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('path', ['/etc/passwd', 'sapl/public//etc/passwd'])
def test_caminho_absoluto(rf, path):
    request = rf.get('/media/' + path)
    request.user = AnonymousUser()

    with pytest.raises(Http404):
        media(request, path)


@pytest.mark.django_db(transaction=False)
def test_modelo_protegido_fora_de_private_e_public(client):
    _config('O')
    path = 'sapl/outra/documentoadministrativo/2026/1/texto.pdf'
    baker.make(DocumentoAdministrativo, restrito=True, texto_integral=path)

    assert _get(client, path).status_code == 404


@pytest.mark.django_db(transaction=False)
def test_senha_fraca_nao_redireciona_media(client):
    _login(client, 'fraca')
    session = client.session
    session['weak_password'] = True
    session.save()

    response = _get(client, 'sapl/public/casalegislativa/logotipo.png')

    assert response.status_code == 200
    assert response.has_header('X-Accel-Redirect')


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('estado,perfil,pode_ver', GRADE_PROPOSICAO)
def test_proposicao_texto(client, settings, tmp_path, estado, perfil,
                          pode_ver):
    settings.MEDIA_ROOT = str(tmp_path)
    arquivo = tmp_path / PROPOSICAO_PATH
    arquivo.parent.mkdir(parents=True)
    arquivo.write_bytes(b'%PDF-1.4 proposicao')
    _login_proposicao(client, perfil, _proposicao(estado))
    pk = Proposicao.objects.get(texto_original=PROPOSICAO_PATH).pk

    response = client.get('/proposicao/texto/%s' % pk)

    if pode_ver:
        assert response.status_code == 200
        assert response.content == b'%PDF-1.4 proposicao'
    else:
        assert response.status_code == 302
        assert response['Location'] == '/proposicao/%s' % pk


def test_nginx_envia_ao_django_todos_os_caminhos_protegidos():
    caminho = os.path.join(settings.PROJECT_DIR, 'docker', 'config',
                           'nginx', 'sapl.conf')
    with open(caminho) as f:
        conf = f.read()
    regex = re.search(r'location ~\*? \^/media/sapl/\(private/\|'
                      r'\[\^/\]\+/\(([a-z|]+)\)/\)', conf)

    assert regex, 'location de arquivos protegidos não encontrada'
    no_nginx = set(regex.group(1).split('|'))
    assert set(RESOLVEDORES) | set(MODELOS_DE_SESSAO) <= no_nginx
    assert conf.index(regex.group(0)) < conf.index('location /media/ {')


def test_nginx_forca_download_das_extensoes_ativas():
    caminho = os.path.join(settings.PROJECT_DIR, 'docker', 'config',
                           'nginx', 'sapl.conf')
    with open(caminho) as f:
        conf = f.read()
    regex = re.search(r'location ~\*? \^/media/\.\+\\\.\(([a-z?|]+)\)\$',
                      conf)

    assert regex, 'location de extensões ativas não encontrada'
    no_nginx = set()
    for ext in regex.group(1).split('|'):
        if ext.endswith('?'):
            no_nginx |= {ext[:-2], ext[:-1]}
        else:
            no_nginx.add(ext)
    assert {'.' + e for e in no_nginx} == EXTENSOES_ATIVAS
