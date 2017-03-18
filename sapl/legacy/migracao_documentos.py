import os
import re
from glob import glob

from sapl.base.models import CasaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.settings import MEDIA_ROOT

# MIGRAÇÃO DE DOCUMENTOS  ###################################################

DOCS = {
    CasaLegislativa: (
        'logotipo',
        'props_sapl/logo_casa.gif',
        'casa/logotipo/logo_casa.gif'),
    Parlamentar: (
        'fotografia',
        'parlamentar/fotos/{}_foto_parlamentar',
        'parlamentar/{0}/{0}_foto_parlamentar'),
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


def migrar_docs_logo():
    _, origem, destino = DOCS[CasaLegislativa]
    props_sapl = os.path.dirname(origem)
    # a pasta props_sapl deve conter apenas o origem e metadatas!
    assert set(os.listdir(em_media(props_sapl))) == {
        'logo_casa.gif', '.metadata', 'logo_casa.gif.metadata'}
    mover_documento(origem, destino)
    casa = CasaLegislativa.objects.first()
    casa.logotipo = destino
    casa.save()


def migrar_docs_por_ids(tipo):
    campo, base_origem, base_destino = DOCS[tipo]
    origens = glob.glob(em_media(base_origem.format('*')))

    def get_id(caminho):
        match = re.match('.*/' + base_origem.format('(\d+)'), caminho)
        return int(match.group(1))

    for origem in origens:
        id = get_id(origem)
        destino = base_destino.format(id)
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
