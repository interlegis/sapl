import mimetypes
import os
import re

import yaml

import magic
from sapl.base.models import CasaLegislativa
from sapl.legacy.migration import exec_legado, warn
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
    'text/xml': '.xml',
    'application/zip': '.zip',
    'image/jpeg': '.jpeg',
    'image/png': '.png',
    'text/html': '.html',
    'text/rtf': '.rtf',
    'text/x-python': '.py',
    'text/plain': '.txt',

    # sem extensao
    'application/octet-stream': '',  # binário
    'inode/x-empty': '',  # vazio
}

DOCS = {
    CasaLegislativa: [
        ('logotipo',
         'props_sapl/logo_casa.gif',
         'casa/logotipo/logo_casa.gif')
    ],
    Parlamentar: [
        ('fotografia',
         'parlamentar/fotos/{}_foto_parlamentar',
         'public/parlamentar/{0}/{0}_foto_parlamentar{1}')
    ],
    MateriaLegislativa: [
        ('texto_original',
         'materia/{}_texto_integral',
         'public/materialegislativa/{2}/{0}/{0}_texto_integral{1}')
    ],
    DocumentoAcessorio: [
        ('arquivo',
         'materia/{}',
         'public/documentoacessorio/{2}/{0}/{0}{1}')
    ],
    NormaJuridica: [
        ('texto_integral',
         'norma_juridica/{}_texto_integral',
         'public/normajuridica/{2}/{0}/{0}_texto_integral{1}')
    ],
    SessaoPlenaria: [
        ('upload_ata',
         'ata_sessao/{}_ata_sessao',
         'public/sessaoplenaria/{0}/ata/{0}_ata_sessao{1}'),
        ('upload_anexo',
         'anexo_sessao/{}_texto_anexado',
         'public/sessaoplenaria/{0}/anexo/{0}_texto_anexado{1}')
    ],
    Proposicao: [
        ('texto_original',
         'proposicao/{}',
         'private/proposicao/{0}/{0}{1}')
    ],
    DocumentoAdministrativo: [
        ('texto_integral',
         'administrativo/{}_texto_integral',
         'private/documentoadministrativo/{0}/{0}_texto_integral{1}')
    ],
    DocumentoAcessorioAdministrativo: [
        ('arquivo',
         'administrativo/{}',
         'private/documentoacessorioadministrativo/{0}/'
         '{0}_acessorio_administrativo{1}')
    ],
}

DOCS = {model: [(campo,
                 os.path.join('sapl_documentos', origem),
                 os.path.join('sapl', destino))
                for campo, origem, destino in campos]
        for model, campos in DOCS.items()}


def em_media(caminho):
    return os.path.join(MEDIA_ROOT, caminho)


def mover_documento(origem, destino):
    origem, destino = [em_media(c) if not os.path.isabs(c) else c
                       for c in (origem, destino)]
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    os.rename(origem, destino)


def migrar_propriedades_da_casa():
    print('#### Migrando propriedades da casa ####')
    caminho = em_media('sapl_documentos/propriedades.yaml')
    with open(caminho, 'r') as arquivo:
        propriedades = yaml.safe_load(arquivo)
    casa = CasaLegislativa.objects.first()
    if not casa:
        casa = CasaLegislativa()
    campos_para_propriedades = [('codigo', 'cod_casa'),
                                ('nome', 'nom_casa'),
                                ('sigla', 'sgl_casa'),
                                ('endereco', 'end_casa'),
                                ('cep', 'num_cep'),
                                ('telefone', 'num_tel'),
                                ('fax', 'num_fax'),
                                ('endereco_web', 'end_web_casa'),
                                ('email', 'end_email_casa'),
                                ('sigla', 'sgl_casa'),
                                ('informacao_geral', 'txt_informacao_geral')]
    for campo, prop in campos_para_propriedades:
        setattr(casa, campo, propriedades[prop])
    # Localidade
    sql_localidade = '''
        select nom_localidade, sgl_uf from localidade
        where cod_localidade = {}'''.format(propriedades['cod_localidade'])
    [(casa.municipio, casa.uf)] = exec_legado(sql_localidade)
    casa.save()


def migrar_logotipo_da_casa():
    print('#### Migrando logotipo da casa ####')
    [(_, origem, destino)] = DOCS[CasaLegislativa]
    props_sapl = os.path.dirname(origem)

    # a pasta props_sapl deve conter apenas o origem e metadatas!
    # Edit: Aparentemente há diretório que contém properties ao invés de
    # metadata. O assert foi modificado para essa situação.
    sobrando = set(os.listdir(em_media(props_sapl))) - {
        'logo_casa.gif', '.metadata', 'logo_casa.gif.metadata',
        '.properties', 'logo_casa.gif.properties', '.objects'}

    if sobrando:
        warn('Os seguintes arquivos da pasta props_sapl foram ignorados: ' +
             ', '.join(sobrando))

    mover_documento(origem, destino)
    casa = CasaLegislativa.objects.first()
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


def migrar_docs_por_ids(model):
    for campo, base_origem, base_destino in DOCS[model]:
        print('#### Migrando {} de {} ####'.format(campo, model.__name__))

        dir_origem, nome_origem = os.path.split(em_media(base_origem))
        pat = re.compile('^{}\.\w+$'.format(nome_origem.format('(\d+)')))

        if not os.path.isdir(dir_origem):
            print('  >>> O diretório {} não existe! Abortado.'.format(
                dir_origem))
            continue

        for arq in os.listdir(dir_origem):
            match = pat.match(arq)
            if match:
                # associa documento ao objeto
                origem = os.path.join(dir_origem, match.group(0))
                id = match.group(1)
                try:
                    obj = model.objects.get(pk=id)
                except model.DoesNotExist:
                    msg = '  {} (pk={}) não encontrado para documento em [{}]'
                    print(msg.format(
                        model.__name__, id, origem))
                else:
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


def migrar_documentos():
    # aqui supomos que uma pasta chamada sapl_documentos está em MEDIA_ROOT
    # com o conteúdo da pasta de mesmo nome do zope
    # Os arquivos da pasta serão MOVIDOS para a nova estrutura e a pasta será
    # apagada
    #
    # Isto significa que para rodar novamente esta função é preciso
    # restaurar a pasta sapl_documentos ao estado inicial

    # esta ordem é importante
    migrar_propriedades_da_casa()
    migrar_logotipo_da_casa()

    for model in [
        Parlamentar,
        MateriaLegislativa,
        DocumentoAcessorio,
        NormaJuridica,
        SessaoPlenaria,
        Proposicao,
        DocumentoAdministrativo,
        DocumentoAcessorioAdministrativo,
    ]:
        migrar_docs_por_ids(model)

    sobrando = [os.path.join(dir, file)
                for (dir, _, files) in os.walk(em_media('sapl_documentos'))
                for file in files]
    if sobrando:
        print('\n#### Encerrado ####\n\n'
              '{} documentos sobraram sem ser migrados!!!'.format(
                  len(sobrando)))
        for doc in sobrando:
            print('  {}'. format(doc))
