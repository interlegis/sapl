import mimetypes
import os
import re
from glob import glob

import yaml

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


def get_ano(obj):
    return [obj.ano]


def ___(obj):
    return []


DOCS = {
    CasaLegislativa: [
        ('logotipo',
         'props_sapl/{}.*',
         'public/casa/logotipo/',
         ___)
    ],
    Parlamentar: [
        ('fotografia',
         'parlamentar/fotos/{}_foto_parlamentar',
         'public/parlamentar/{0}/',
         ___)
    ],
    MateriaLegislativa: [
        ('texto_original',
         'materia/{}_texto_integral',
         'public/materialegislativa/{1}/{0}/',
         get_ano)
    ],
    DocumentoAcessorio: [
        ('arquivo',
         'materia/{}',
         'public/documentoacessorio/{1}/{0}/',
         lambda obj: [obj.materia.ano])
    ],
    NormaJuridica: [
        ('texto_integral',
         'norma_juridica/{}_texto_integral',
         'public/normajuridica/{1}/{0}/',
         get_ano)
    ],
    SessaoPlenaria: [
        ('upload_ata',
         'ata_sessao/{}_ata_sessao',
         'public/sessaoplenaria/{0}/ata/',
         ___),
        ('upload_anexo',
         'anexo_sessao/{}_texto_anexado',
         'public/sessaoplenaria/{0}/anexo/',
         ___)
    ],
    Proposicao: [
        ('texto_original',
         'proposicao/{}',
         'private/proposicao/{0}/',
         get_ano)
    ],
    DocumentoAdministrativo: [
        ('texto_integral',
         'administrativo/{}_texto_integral',
         'private/documentoadministrativo/{0}/',
         get_ano)
    ],
    DocumentoAcessorioAdministrativo: [
        ('arquivo',
         'administrativo/{}',
         'private/documentoacessorioadministrativo/{0}/',
         ___)
    ],
}

DOCS = {model: [(campo,
                 os.path.join('sapl_documentos', origem),
                 os.path.join('sapl', destino),
                 get_extra_args)
                for campo, origem, destino, get_extra_args in campos]
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

    print('.... Migrando logotipo da casa ....')
    [(_, origem, destino, __)] = DOCS[CasaLegislativa]
    # a extensão do logo pode ter sido ajustada pelo tipo real do arquivo
    id_logo = os.path.splitext(propriedades['id_logo'])[0]
    [origem] = glob(em_media(origem.format(id_logo)))
    destino = os.path.join(destino, os.path.basename(origem))
    mover_documento(origem, destino)
    casa.logotipo = destino
    casa.save()
    os.remove(caminho)


def migrar_docs_por_ids(model):
    for campo, base_origem, base_destino, get_extra_args in DOCS[model]:
        print('#### Migrando {} de {} ####'.format(campo, model.__name__))

        dir_origem, nome_origem = os.path.split(em_media(base_origem))
        nome_origem = nome_origem.format('(\d+)')
        pat = re.compile('^{}\.\w+$'.format(nome_origem))

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
                    print(msg.format(model.__name__, id, origem))
                else:
                    destino = os.path.join(
                        base_destino.format(id, *get_extra_args(obj)),
                        os.path.basename(origem))
                    mover_documento(origem, destino)
                    setattr(obj, campo, destino)
                    obj.save()


def migrar_documentos():
    # aqui supomos que uma pasta chamada sapl_documentos está em MEDIA_ROOT
    # com o conteúdo da pasta de mesmo nome do zope
    # Os arquivos da pasta serão MOVIDOS para a nova estrutura!
    # A pasta, após conferência do que não foi migrado, deve ser apagada.
    #
    # Isto significa que para rodar novamente esta função é preciso
    # restaurar a pasta sapl_documentos ao estado inicial

    migrar_propriedades_da_casa()

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
