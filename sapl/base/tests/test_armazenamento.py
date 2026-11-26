import errno
import json
import os
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from model_bakery import baker
import pytest

from sapl.armazenamento import (ArmazenamentoArquivos, FalhaGravacaoArquivo,
                                mensagem_falha_gravacao)
from sapl.middleware.falha_gravacao import FalhaGravacaoArquivoMiddleware
from sapl.norma.models import NormaJuridica, TipoNormaJuridica

PDF = b'%PDF-1.4\n%%EOF\n'


def sem_espaco(*args, **kwargs):
    raise OSError(errno.ENOSPC, 'No space left on device')


class ConteudoInterrompido(ContentFile):
    """Grava um pedaço e falha, como uma gravação interrompida pelo disco
    cheio."""

    def chunks(self, chunk_size=None):
        yield b'%PDF-1.4 parte gravada antes da falha'
        sem_espaco()


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    return tmp_path


def test_storage_remove_arquivo_parcial(media):
    storage = ArmazenamentoArquivos(location=str(media))

    with pytest.raises(FalhaGravacaoArquivo) as e:
        storage.save('sapl/public/normajuridica/2026/1/lei.pdf',
                     ConteudoInterrompido(b''))

    assert e.value.errno == errno.ENOSPC
    assert not os.path.exists(
        media / 'sapl/public/normajuridica/2026/1/lei.pdf')


def test_storage_nao_remove_arquivo_que_ja_existia(media):
    storage = ArmazenamentoArquivos(location=str(media))
    existente = media / 'lei.pdf'
    existente.write_bytes(PDF)

    with pytest.raises(FalhaGravacaoArquivo):
        storage._save('lei.pdf', ConteudoInterrompido(b''))

    assert existente.read_bytes() == PDF


def test_storage_sem_permissao_no_diretorio(media):
    storage = ArmazenamentoArquivos(location=str(media))
    negado = OSError(errno.EACCES, 'Permission denied')

    with mock.patch('os.makedirs', side_effect=negado):
        with pytest.raises(FalhaGravacaoArquivo) as e:
            storage.save('sapl/public/x/lei.pdf', ContentFile(PDF))

    assert e.value.errno == errno.EACCES
    assert 'sem permissão de escrita' in mensagem_falha_gravacao(e.value)


def dados_norma():
    return dict(tipo=baker.make(TipoNormaJuridica), numero='1', ano=2026,
                data='2026-01-01', esfera_federacao='M', ementa='Ementa')


@pytest.mark.django_db
def test_inclusao_com_arquivo_por_create(media):
    """
    QuerySet.create() passa force_insert=True ao save. A segunda gravação,
    que guarda o arquivo, não pode repetir o insert da mesma pk.
    """
    norma = NormaJuridica.objects.create(
        texto_integral=SimpleUploadedFile('lei.pdf', PDF), **dados_norma())

    norma.refresh_from_db()
    assert '/{}/lei.pdf'.format(norma.pk) in norma.texto_integral.name
    assert os.path.exists(norma.texto_integral.path)


@pytest.mark.django_db
def test_inclusao_desfeita_se_o_arquivo_nao_for_gravado(media):
    with mock.patch('django.core.files.storage.FileSystemStorage._save',
                    side_effect=sem_espaco):
        norma = NormaJuridica(
            texto_integral=SimpleUploadedFile('lei.pdf', PDF), **dados_norma())
        with pytest.raises(FalhaGravacaoArquivo):
            norma.save()

    assert not NormaJuridica.objects.exists()
    assert norma.pk is None
    assert norma._state.adding
    assert norma.texto_integral.name == 'lei.pdf'


def requisicao(path, **extra):
    request = RequestFactory().post(path, **extra)
    request.user = AnonymousUser()
    request.request_id = 'abc123'
    return request


def test_middleware_responde_json_na_api():
    middleware = FalhaGravacaoArquivoMiddleware(lambda r: None)
    erro = FalhaGravacaoArquivo(errno.ENOSPC, 'No space left on device',
                                'lei.pdf')

    response = middleware.process_exception(
        requisicao('/api/norma/normajuridica/'), erro)

    assert response.status_code == 507
    corpo = json.loads(response.content)
    assert 'espaço de armazenamento do servidor está esgotado' in \
        corpo['detail']
    assert corpo['request_id'] == 'abc123'
    assert 'lei.pdf' not in corpo['detail']


@pytest.mark.django_db
def test_middleware_responde_pagina_na_interface():
    middleware = FalhaGravacaoArquivoMiddleware(lambda r: None)
    erro = FalhaGravacaoArquivo(errno.EROFS, 'Read-only file system',
                                'lei.pdf')

    response = middleware.process_exception(requisicao('/norma/create'),
                                            erro)

    assert response.status_code == 500
    conteudo = response.content.decode()
    assert 'Não foi possível gravar o arquivo' in conteudo
    assert 'sem permissão de escrita' in conteudo
    assert 'abc123' in conteudo


@pytest.mark.parametrize('erro', [
    ValueError('outro erro'),
    OSError(errno.EACCES, 'Permission denied'),  # leitura, não gravação
])
def test_middleware_ignora_outros_erros(erro):
    middleware = FalhaGravacaoArquivoMiddleware(lambda r: None)

    assert middleware.process_exception(requisicao('/api/x/'), erro) is None


def test_middleware_trata_disco_cheio_fora_do_storage():
    """O arquivo temporário do upload também pode esbarrar no disco cheio."""
    middleware = FalhaGravacaoArquivoMiddleware(lambda r: None)

    response = middleware.process_exception(
        requisicao('/api/x/'), OSError(errno.ENOSPC, 'No space left'))

    assert response.status_code == 507
