from django.core.exceptions import ValidationError
import pytest

from .utils import (listify, rejeita_conteudo_ativo,
                    restringe_tipos_de_arquivo_txt, tipo_ativo,
                    validar_arquivo)


def test_listify():

    @listify
    def gen():
        yield 1
        yield 2
    assert [1, 2] == gen()


def _upload(nome, conteudo):
    import io
    from django.core.files.uploadedfile import InMemoryUploadedFile
    return InMemoryUploadedFile(io.BytesIO(conteudo), 'arquivo', nome, None,
                                len(conteudo), None)


def _odt():
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr(zipfile.ZipInfo('mimetype'),
                   'application/vnd.oasis.opendocument.text')
        z.writestr('content.xml', '<office:document-content/>')
    return buf.getvalue()


PNG = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
       b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89')

ATIVOS = [
    ('x.html', b'%PDF-1.4\n<html><script>alert(1)</script></html>'),
    ('x.html', b'<html><script>alert(1)</script></html>'),
    ('x.svg', b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'),
    ('x.XHTML', b'%PDF-1.4'),
    ('x.xht', b'%PDF-1.4\n<html><script>alert(1)</script></html>'),
    ('x.rdf', b'%PDF-1.4'),
    ('x.kml', b'<kml><script>alert(1)</script></kml>'),
    ('x.pdf', b'<!DOCTYPE html><html><script>alert(1)</script></html>'),
]


@pytest.mark.parametrize('nome,conteudo', ATIVOS)
def test_validar_arquivo_rejeita_conteudo_ativo(nome, conteudo):
    with pytest.raises(ValidationError):
        validar_arquivo(_upload(nome, conteudo), 'Arquivo')


@pytest.mark.parametrize('nome,conteudo', ATIVOS)
def test_restringe_tipos_rejeita_conteudo_ativo(nome, conteudo):
    with pytest.raises(ValidationError):
        restringe_tipos_de_arquivo_txt(_upload(nome, conteudo))


@pytest.mark.parametrize('nome,conteudo', [
    ('a.pdf', b'%PDF-1.4\n%%EOF'),
    ('a.csv', b'nome;valor\nx;1\n'),
    ('a.odt', _odt()),
    ('a.png', PNG),
    ('a.xlsx', b'PK\x03\x04' + b'\x00' * 64),
])
def test_validar_arquivo_aceita_tipos_comuns(nome, conteudo):
    validar_arquivo(_upload(nome, conteudo), 'Arquivo')


@pytest.mark.parametrize('nome,conteudo', [
    ('a.pdf', b'%PDF-1.4\n%%EOF'),
    ('a.csv', b'nome;valor\nx;1\n'),
    ('a.odt', _odt()),
])
def test_restringe_tipos_aceita_documentos(nome, conteudo):
    restringe_tipos_de_arquivo_txt(_upload(nome, conteudo))


def test_validar_arquivo_ignora_arquivo_ja_gravado():
    from django.db.models.fields.files import FieldFile
    from sapl.protocoloadm.models import DocumentoAdministrativo
    campo = DocumentoAdministrativo._meta.get_field('texto_integral')
    antigo = FieldFile(None, campo,
                       'sapl/private/documentoadministrativo/x.html')
    rejeita_conteudo_ativo(antigo)


@pytest.mark.parametrize('mime,ativo', [
    ('text/html', True), ('application/xhtml+xml', True),
    ('application/rdf+xml', True), ('text/xml', True),
    ('application/javascript', True), ('image/svg+xml', True),
    ('application/pdf', False), ('image/png', False), ('text/csv', False),
    ('application/vnd.openxmlformats-officedocument.wordprocessingml.document',
     False),
    (None, False),
])
def test_tipo_ativo(mime, ativo):
    assert tipo_ativo(mime) is ativo
