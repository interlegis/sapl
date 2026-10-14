from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
import pytest

from sapl.base.models import AppConfig
from sapl.materia.models import (Proposicao, TipoMateriaLegislativa,
                                 TipoProposicao)
from sapl.utils import SEPARADOR_HASH_PROPOSICAO, gerar_hash_arquivo

PROPOSICAO_PATH = 'sapl/private/proposicao/2026/1/proposicao.pdf'
PERMS_DOCADM = ['add_documentoadministrativo',
                'change_documentoadministrativo',
                'detail_documentoadministrativo']


def _login(client, app_label, *codenames):
    user = baker.make(get_user_model(), username=app_label)
    user.user_permissions.add(*Permission.objects.filter(
        content_type__app_label=app_label, codename__in=codenames))
    client.force_login(user)
    return user


def _login_docadm(client):
    user = _login(client, 'protocoloadm', *PERMS_DOCADM)
    assert user.has_module_perms('protocoloadm')


def _login_protocolo(client):
    _login(client, 'materia', 'detail_proposicao_enviada')


def _proposicao_enviada(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    baker.make(AppConfig)
    arquivo = tmp_path / PROPOSICAO_PATH
    arquivo.parent.mkdir(parents=True)
    arquivo.write_bytes(b'%PDF-1.4 proposicao')
    tipo = baker.make(
        TipoProposicao,
        content_type=ContentType.objects.get_for_model(TipoMateriaLegislativa),
        object_id=baker.make(TipoMateriaLegislativa).pk)
    proposicao = baker.make(Proposicao, tipo=tipo,
                            texto_original=PROPOSICAO_PATH,
                            data_envio=timezone.now())
    hasher = gerar_hash_arquivo(str(arquivo), str(proposicao.pk))
    return proposicao, hasher[1:].split(SEPARADOR_HASH_PROPOSICAO)[0]


def _url_confirmar(proposicao, hash_):
    return reverse('sapl.materia:proposicao-confirmar',
                   kwargs={'hash': hash_, 'pk': proposicao.pk})


@pytest.mark.django_db(transaction=False)
def test_receber_exige_permissao_de_proposicao(client):
    _login_docadm(client)
    url = reverse('sapl.materia:receber-proposicao')

    assert client.get(url).status_code == 403


@pytest.mark.django_db(transaction=False)
def test_receber_operador_de_protocolo(client):
    _login_protocolo(client)
    url = reverse('sapl.materia:receber-proposicao')

    assert client.get(url).status_code == 200


@pytest.mark.django_db(transaction=False)
def test_confirmar_exige_permissao_de_proposicao(client, settings, tmp_path):
    proposicao, hash_ = _proposicao_enviada(settings, tmp_path)
    _login_docadm(client)

    response = client.get(_url_confirmar(proposicao, hash_))

    assert response.status_code == 403


@pytest.mark.django_db(transaction=False)
def test_confirmar_operador_de_protocolo_ve_texto(client, settings,
                                                  tmp_path):
    settings.DEBUG = False
    proposicao, hash_ = _proposicao_enviada(settings, tmp_path)
    _login_protocolo(client)

    response = client.get(_url_confirmar(proposicao, hash_))

    assert response.status_code == 200
    assert proposicao.texto_original.url.encode() in response.content
    texto = client.get(proposicao.texto_original.url)
    assert texto.status_code == 200
    assert texto['X-Accel-Redirect'] == '/media-interna/' + PROPOSICAO_PATH
