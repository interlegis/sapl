import mimetypes
import os
import re

import magic

from sapl.base.models import CasaLegislativa
from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.settings import MEDIA_ROOT

# MIGRAÇÃO DE DOCUMENTOS  ###################################################
EXTENSOES = {
    'application/msword': '.doc',
    'application/pdf': '.pdf',
    'application/vnd.oasis.opendocument.text': '.odt',
    'application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.document': '.docx',
    'application/xml': '.xml',
    'application/zip': '.zip',
    'image/jpeg': '.jpeg',
    'image/png': '.png',
    'text/html': '.html',
}

DOCS = {
    CasaLegislativa: (
        'logotipo',
        'props_sapl/logo_casa.gif',
        'casa/logotipo/logo_casa.gif'),
    Parlamentar: (
        'fotografia',
        'parlamentar/fotos/{}_foto_parlamentar',
        'parlamentar/{0}/{0}_foto_parlamentar{1}'),
    MateriaLegislativa: (
        'texto_original',
        'materia/{}_texto_integral',
        'materialegislativa/{0}/{0}_texto_integral{1}'),
    DocumentoAcessorio: (
        'arquivo',
        'materia/{}',
        'documentoacessorio/{0}/{0}{1}'),
}

DOCS = {tipo: (campo,
               os.path.join('sapl_documentos', origem),
               os.path.join('sapl', destino))
        for tipo, (campo, origem, destino) in DOCS.items()}


def em_media(caminho):
    return os.path.join(MEDIA_ROOT, caminho)


def mover_documento(origem, destino):
    origem, destino = [em_media(c) if not os.path.isabs(c) else c
                       for c in (origem, destino)]
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    os.rename(origem, destino)


def get_casa_legislativa():
    casa = CasaLegislativa.objects.first()
    if not casa:
        casa = CasaLegislativa.objects.create(**{k: 'PREENCHER...' for k in [
            'codigo', 'nome', 'sigla', 'endereco', 'cep', 'municipio', 'uf',
        ]})
    return casa


def migrar_docs_logo():
    _, origem, destino = DOCS[CasaLegislativa]
    props_sapl = os.path.dirname(origem)
    # a pasta props_sapl deve conter apenas o origem e metadatas!
    assert set(os.listdir(em_media(props_sapl))) == {
        'logo_casa.gif', '.metadata', 'logo_casa.gif.metadata'}
    mover_documento(origem, destino)
    casa = get_casa_legislativa()
    casa.logotipo = destino
    casa.save()


def get_extensao(caminho):
    mime = magic.from_file(caminho, mime=True)
    try:
        return EXTENSOES[mime]
    except KeyError as e:
        raise Exception('\n'.join([
            'Extensão não conhecida. Algumas possibilidades são:', ] +
            ["    '{}': '{}',".format(mime, ext)
             for ext in mimetypes.guess_all_extensions(mime)] +
            ['Atualize o código do dicionário EXTENSOES!']
        )) from e


def migrar_docs_por_ids(tipo):
    campo, base_origem, base_destino = DOCS[tipo]

    dir_origem, nome_origem = os.path.split(em_media(base_origem))
    pat = re.compile('^{}$'.format(nome_origem.format('(\d+)')))
    for arq in os.listdir(dir_origem):
        match = pat.match(arq)
        if match:
            origem = os.path.join(dir_origem, match.group(0))
            id = match.group(1)
            extensao = get_extensao(origem)
            destino = base_destino.format(id, extensao)
            mover_documento(origem, destino)

            obj = tipo.objects.get(pk=id)
            setattr(obj, campo, destino)
            obj.save()


def migrar_documentos():
    # aqui supomos que uma pasta chamada sapl_documentos está em MEDIA_ROOT
    # com o conteúdo da pasta de mesmo nome do zope
    # Os arquivos da pasta serão movidos para a nova estrutura e a pasta será
    # apagada
    migrar_docs_logo()
    migrar_docs_por_ids(Parlamentar)
    migrar_docs_por_ids(MateriaLegislativa)
    migrar_docs_por_ids(DocumentoAcessorio)
