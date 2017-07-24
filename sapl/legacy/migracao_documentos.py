import mimetypes
import os
import re

import magic
from django.db.models.signals import post_delete, post_save

from sapl.base.models import CasaLegislativa
from sapl.materia.models import (DocumentoAcessorio, MateriaLegislativa,
                                 Proposicao)
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import (DocumentoAcessorioAdministrativo,
                                      DocumentoAdministrativo)
from sapl.sessao.models import SessaoPlenaria
from sapl.settings import MEDIA_ROOT

# MIGRAÇÃO DE DOCUMENTOS  ###################################################
EXTENSOES = {
    'application/msword': '.doc',
    'application/pdf': '.pdf',
    'application/vnd.oasis.opendocument.text': '.odt',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',  # noqa
    'application/xml': '.xml',
    'application/zip': '.zip',
    'image/jpeg': '.jpeg',
    'image/png': '.png',
    'text/html': '.html',
    'text/rtf': '.rtf',
    'text/x-python': '.py',
    'text/plain': '.ksh',
    'text/plain': '.c',
    'text/plain': '.h',
    'text/plain': '.txt',
    'text/plain': '.bat',
    'text/plain': '.pl',
    'text/plain': '.asc',
    'text/plain': '.text',
    'text/plain': '.pot',
    'text/plain': '.brf',
    'text/plain': '.srt',

    # sem extensao
    'application/octet-stream': '',  # binário
    'inode/x-empty': '',  # vazio
}

DOCS = {
    CasaLegislativa: [(
        'logotipo',
        'props_sapl/logo_casa.gif',
        'casa/logotipo/logo_casa.gif')],
    Parlamentar: [(
        'fotografia',
        'parlamentar/fotos/{}_foto_parlamentar',
        'public/parlamentar/{0}/{0}_foto_parlamentar{1}')],
    MateriaLegislativa: [(
        'texto_original',
        'materia/{}_texto_integral',
        'public/materialegislativa/{2}/{0}/{0}_texto_integral{1}')],
    DocumentoAcessorio: [(
        'arquivo',
        'materia/{}',
        'public/documentoacessorio/{2}/{0}/{0}{1}')],
    NormaJuridica: [(
        'texto_integral',
        'norma_juridica/{}_texto_integral',
        'public/normajuridica/{2}/{0}/{0}_texto_integral{1}')],
    SessaoPlenaria: [
        ('upload_ata',
         'ata_sessao/{}_ata_sessao',
         'public/sessaoplenaria/{0}/ata/{0}_ata_sessao{1}'),
        ('upload_anexo',
         'anexo_sessao/{}_texto_anexado',
         'public/sessaoplenaria/{0}/anexo/{0}_texto_anexado{1}')
    ],
    Proposicao: [(
        'texto_original',
        'proposicao/{}',
        'private/proposicao/{0}/{0}{1}')],
    DocumentoAdministrativo: [(
        'texto_integral',
        'administrativo/{}_texto_integral',
        'private/documentoadministrativo/{0}/{0}_texto_integral{1}')
    ],
    DocumentoAcessorioAdministrativo: [(
        'arquivo',
        'administrativo/{}',
        'private/documentoacessorioadministrativo/{0}/{0}_acessorio_administrativo{1}')
    ],
}

DOCS = {tipo: [(campo,
                os.path.join('sapl_documentos', origem),
                os.path.join('sapl', destino))
               for campo, origem, destino in campos]
        for tipo, campos in DOCS.items()}


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
    print('#### Migrando logotipo da casa ####')
    [(_, origem, destino)] = DOCS[CasaLegislativa]
    props_sapl = os.path.dirname(origem)

    # a pasta props_sapl deve conter apenas o origem e metadatas!
    # Edit: Aparentemente há diretório que contém properties ao invés de
    # metadata. O assert foi modificado para essa situação.
    assert set(os.listdir(em_media(props_sapl))) < {
        'logo_casa.gif', '.metadata', 'logo_casa.gif.metadata',
        '.properties', 'logo_casa.gif.properties', '.objects'}

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
            'Extensão não conhecida para o arquivo:',
            caminho,
            'E mimetype:',
            mime,
            ' Algumas possibilidades são:', ] +
            ["    '{}': '{}',".format(mime, ext)
             for ext in mimetypes.guess_all_extensions(mime)] +
            ['Atualize o código do dicionário EXTENSOES!']
        )) from e


def migrar_docs_por_ids(tipo):
    for campo, base_origem, base_destino in DOCS[tipo]:
        print('#### Migrando {} de {} ####'.format(campo, tipo.__name__))

        dir_origem, nome_origem = os.path.split(em_media(base_origem))
        pat = re.compile('^{}$'.format(nome_origem.format('(\d+)')))

        if not os.path.isdir(dir_origem):
            print('  >>> O diretório {} não existe! Abortado.'.format(
                dir_origem))
            continue

        for arq in os.listdir(dir_origem):
            match = pat.match(arq)
            if match:
                # associa documento ao objeto
                try:
                    origem = os.path.join(dir_origem, match.group(0))
                    id = match.group(1)
                    obj = tipo.objects.get(pk=id)

                    extensao = get_extensao(origem)
                    if hasattr(obj, "ano"):
                        destino = base_destino.format(id, extensao, obj.ano)
                    elif isinstance(obj, DocumentoAcessorio):
                        destino = base_destino.format(
                            id, extensao, obj.materia.ano)
                    else:
                        destino = base_destino.format(id, extensao)
                    mover_documento(origem, destino)

                    setattr(obj, campo, destino)
                    obj.save()
                except tipo.DoesNotExist:
                    msg = '  {} (pk={}) não encontrado para documento em [{}]'
                    print(msg.format(
                        tipo.__name__, id, destino))


def desconecta_sinais_indexacao():
    post_save.disconnect(NormaJuridica)
    post_save.disconnect(DocumentoAcessorio)
    post_save.disconnect(MateriaLegislativa)
    post_delete.disconnect(NormaJuridica)
    post_delete.disconnect(DocumentoAcessorio)
    post_delete.disconnect(MateriaLegislativa)


def conecta_sinais_indexacao():
    post_save.connect(NormaJuridica)
    post_save.connect(DocumentoAcessorio)
    post_save.connect(MateriaLegislativa)
    post_delete.connect(NormaJuridica)
    post_delete.connect(DocumentoAcessorio)
    post_delete.connect(MateriaLegislativa)


def migrar_documentos():
    # precisamos excluir os sinais de post_save e post_delete para não que o
    # computador não trave com a criação de threads desnecessárias
    desconecta_sinais_indexacao()

    # aqui supomos que uma pasta chamada sapl_documentos está em MEDIA_ROOT
    # com o conteúdo da pasta de mesmo nome do zope
    # Os arquivos da pasta serão movidos para a nova estrutura e a pasta será
    # apagada
    migrar_docs_logo()
    for tipo in [
        Parlamentar,
        MateriaLegislativa,
        DocumentoAcessorio,
        NormaJuridica,
        SessaoPlenaria,
        Proposicao,
        DocumentoAdministrativo,
      	DocumentoAcessorioAdministrativo,
    ]:
        migrar_docs_por_ids(tipo)

    sobrando = [os.path.join(dir, file)
                for (dir, _, files) in os.walk(em_media('sapl_documentos'))
                for file in files]
    if sobrando:
        print('\n#### Encerrado ####\n\n'
              '{} documentos sobraram sem ser migrados!!!'.format(
                  len(sobrando)))
        for doc in sobrando:
            print('  {}'. format(doc))
            #
    # reconexão dos sinais desligados no inicio da migração de documentos
    conecta_sinais_indexacao()
