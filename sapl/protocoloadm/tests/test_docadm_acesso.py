from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from model_bakery import baker
import pytest

from sapl.base.models import AppConfig
from sapl.protocoloadm.models import DocumentoAdministrativo


@pytest.fixture
def media_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    return tmp_path


def _config(comportamento):
    cache.clear()
    AppConfig.objects.all().delete()
    baker.make(AppConfig, documentos_administrativos=comportamento)


def _documento(restrito):
    documento = baker.make(DocumentoAdministrativo, restrito=restrito)
    documento.texto_integral = SimpleUploadedFile(
        'texto.pdf', b'%PDF-1.4 conteudo', content_type='application/pdf')
    documento.save()
    return documento


def _client(client, perfil):
    if perfil == 'anonimo':
        return client
    user = baker.make(get_user_model(), username=perfil)
    if perfil == 'com_permissao':
        ct = ContentType.objects.get_for_model(DocumentoAdministrativo)
        perm, _ = Permission.objects.get_or_create(
            codename='detail_documentoadministrativo', content_type=ct,
            defaults={'name': 'detail'})
        user.user_permissions.add(perm)
    client.force_login(user)
    return client


ACESSO = [
    # (comportamento, restrito, perfil, pode_ver)
    ('O', False, 'anonimo', True),
    ('O', False, 'sem_permissao', True),
    ('O', False, 'com_permissao', True),
    ('O', True, 'anonimo', False),
    ('O', True, 'sem_permissao', True),
    ('O', True, 'com_permissao', True),
    ('R', False, 'anonimo', False),
    ('R', False, 'sem_permissao', False),
    ('R', False, 'com_permissao', True),
    ('R', True, 'anonimo', False),
    ('R', True, 'sem_permissao', False),
    ('R', True, 'com_permissao', True),
]


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('comportamento,restrito,perfil,pode_ver', ACESSO)
def test_doc_texto_integral_acesso(client, media_tmp, comportamento,
                                   restrito, perfil, pode_ver):
    _config(comportamento)
    documento = _documento(restrito)
    client = _client(client, perfil)

    response = client.get(reverse('sapl.protocoloadm:doc_texto_integral',
                                  kwargs={'pk': documento.pk}))

    assert response.status_code == (200 if pode_ver else 404)


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('comportamento,restrito,perfil,pode_ver', ACESSO)
def test_pdf_docacessorios_acesso(client, media_tmp, comportamento,
                                  restrito, perfil, pode_ver):
    _config(comportamento)
    documento = baker.make(DocumentoAdministrativo, restrito=restrito)
    client = _client(client, perfil)

    response = client.get(reverse('sapl.protocoloadm:merge_docacessorios',
                                  kwargs={'pk': documento.pk}))

    if pode_ver:
        assert response.status_code != 404
    else:
        assert response.status_code == 404


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('url_name', ['doc_texto_integral',
                                      'merge_docacessorios'])
def test_docadm_pk_inexistente(client, url_name):
    _config('O')
    response = client.get(reverse('sapl.protocoloadm:' + url_name,
                                  kwargs={'pk': 999999}))
    assert response.status_code == 404
