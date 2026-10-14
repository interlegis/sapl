import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from model_bakery import baker
import pytest

from sapl.materia.models import (DocumentoAcessorio, MateriaLegislativa,
                                 TipoDocumento)


@pytest.fixture
def dirs(settings, tmp_path, monkeypatch):
    media = tmp_path / 'media'
    temp = tmp_path / 'temp'
    media.mkdir()
    temp.mkdir()
    settings.MEDIA_ROOT = str(media)
    monkeypatch.setattr('sapl.materia.views.MEDIA_ROOT', str(media))
    monkeypatch.setattr('sapl.materia.views.get_tempfile_dir',
                        lambda: str(temp))
    return media, temp


def _post(client, nome, conteudo):
    materias = baker.make(MateriaLegislativa, _quantity=2)
    tipo = baker.make(TipoDocumento, descricao='Parecer')
    client.post(reverse('sapl.materia:acessorio_em_lote'), {
        'materia_id': [m.pk for m in materias],
        'tipo': tipo.descricao,
        'nome': 'Parecer',
        'autor': 'Comissão',
        'data': '12/10/2026',
        'ementa': 'Ementa',
        'arquivo': SimpleUploadedFile(nome, conteudo),
    })
    return materias


@pytest.mark.django_db(transaction=False)
def test_arquivo_invalido_nao_grava_nada(admin_client, dirs):
    media, temp = dirs

    _post(admin_client, 'x.html', b'%PDF-1.4\n<html><script></script>')

    assert not DocumentoAcessorio.objects.exists()
    assert os.listdir(media) == []
    assert os.listdir(temp) == []


@pytest.mark.django_db(transaction=False)
def test_arquivo_valido_copiado_para_cada_materia(admin_client, dirs):
    media, temp = dirs

    materias = _post(admin_client, 'parecer.pdf', b'%PDF-1.4\n%%EOF')

    docs = DocumentoAcessorio.objects.filter(materia__in=materias)
    assert docs.count() == 2
    for doc in docs:
        assert doc.arquivo.name == (
            'sapl/public/documentoacessorio/2026/%s/parecer.pdf' % doc.pk)
        assert (media / doc.arquivo.name).read_bytes() == b'%PDF-1.4\n%%EOF'
    assert os.listdir(media) == ['sapl']
    assert os.listdir(temp) == []
