import errno
import os
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker
import pytest

from sapl.materia.models import (DocumentoAcessorio, MateriaLegislativa,
                                 TipoDocumento)
from sapl.norma.models import NormaJuridica, TipoNormaJuridica

PDF = b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n'


def pdf(nome='texto.pdf'):
    return SimpleUploadedFile(nome, PDF, content_type='application/pdf')


def sem_espaco(*args, **kwargs):
    raise OSError(errno.ENOSPC, 'No space left on device')


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    return tmp_path


@pytest.fixture
def admin(usuario):
    return usuario('admin_upload', is_superuser=True, is_staff=True)


def dados_norma():
    return {'tipo': baker.make(TipoNormaJuridica).pk, 'numero': '10',
            'ano': 2026, 'data': '2026-01-01', 'esfera_federacao': 'M',
            'ementa': 'Ementa de teste'}


@pytest.mark.django_db(transaction=False)
def test_post_multipart_cria_norma_com_arquivo(api, admin, media):
    """
    A inclusão pela API usa QuerySet.create() (force_insert=True). A gravação
    do arquivo, feita num segundo save, não pode repetir o insert.
    """
    dados = dict(dados_norma(), texto_integral=pdf())

    response = api(admin).post('/api/norma/normajuridica/', dados,
                               format='multipart')

    assert response.status_code == 201
    norma = NormaJuridica.objects.get(pk=response.json()['id'])
    assert os.path.exists(norma.texto_integral.path)


@pytest.mark.django_db(transaction=False)
def test_post_multipart_cria_documento_acessorio_com_arquivo(
        api, admin, media):
    materia = baker.make(MateriaLegislativa)
    dados = {'materia': materia.pk, 'tipo': baker.make(TipoDocumento).pk,
             'nome': 'Parecer', 'data': '2026-01-01', 'arquivo': pdf()}

    response = api(admin).post('/api/materia/documentoacessorio/', dados,
                               format='multipart')

    assert response.status_code == 201
    documento = DocumentoAcessorio.objects.get(pk=response.json()['id'])
    assert os.path.exists(documento.arquivo.path)


@pytest.mark.django_db(transaction=False)
def test_patch_com_disco_cheio_responde_507(api, admin, media):
    norma = baker.make(NormaJuridica)

    with mock.patch('django.core.files.storage.FileSystemStorage._save',
                    side_effect=sem_espaco):
        response = api(admin).patch(
            '/api/norma/normajuridica/{}/'.format(norma.pk),
            {'texto_integral': pdf()}, format='multipart')

    assert response.status_code == 507
    assert 'espaço de armazenamento do servidor está esgotado' in \
        response.json()['detail']
    assert response.json()['request_id'] == response['X-Request-ID']
    # o save_base do Django marca a transação do teste para rollback quando a
    # gravação do arquivo falha: o banco não pode mais ser consultado aqui
    assert not [f for _, _, fs in os.walk(media) for f in fs]


@pytest.mark.django_db(transaction=False)
def test_post_com_disco_cheio_nao_deixa_registro(api, admin, media):
    dados = dict(dados_norma(), texto_integral=pdf())

    with mock.patch('django.core.files.storage.FileSystemStorage._save',
                    side_effect=sem_espaco):
        response = api(admin).post('/api/norma/normajuridica/', dados,
                                   format='multipart')

    assert response.status_code == 507
    assert not NormaJuridica.objects.exists()
