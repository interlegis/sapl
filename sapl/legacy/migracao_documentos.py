import os
import re
from glob import glob

import yaml
from django.db import transaction

from sapl.base.models import CasaLegislativa
from sapl.legacy.migracao_dados import exec_legado
from sapl.materia.models import (DocumentoAcessorio, MateriaLegislativa,
                                 Proposicao)
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import (DocumentoAcessorioAdministrativo,
                                      DocumentoAdministrativo)
from sapl.sessao.models import SessaoPlenaria
from sapl.settings import MEDIA_ROOT

# MIGRAÇÃO DE DOCUMENTOS  ###################################################


DOCS = {
    CasaLegislativa: [('logotipo', 'props_sapl/{}.*')],
    Parlamentar: [('fotografia', 'parlamentar/fotos/{}_foto_parlamentar')],
    MateriaLegislativa: [('texto_original', 'materia/{}_texto_integral')],
    DocumentoAcessorio: [('arquivo', 'materia/{}')],
    NormaJuridica: [('texto_integral', 'norma_juridica/{}_texto_integral')],
    SessaoPlenaria: [('upload_pauta', 'pauta_sessao/{}_pauta_sessao'),
                     ('upload_ata', 'ata_sessao/{}_ata_sessao'),
                     ('upload_anexo', 'anexo_sessao/{}_texto_anexado')],
    Proposicao: [('texto_original', 'proposicao/{}')],
    DocumentoAdministrativo: [('texto_integral',
                               'administrativo/{}_texto_integral')],
    DocumentoAcessorioAdministrativo: [('arquivo', 'administrativo/{}')],
}

DOCS = {model: [(campo, os.path.join('sapl_documentos', origem))
                for campo, origem, in campos]
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
    [(campo, origem)] = DOCS[CasaLegislativa]
    # a extensão do logo pode ter sido ajustada pelo tipo real do arquivo
    id_logo = os.path.splitext(propriedades['id_logo'])[0]
    [origem] = glob(em_media(origem.format(id_logo)))
    destino = os.path.join(
        CasaLegislativa._meta.get_field(campo).upload_to,
        os.path.basename(origem))
    mover_documento(origem, destino)
    casa.logotipo = destino
    casa.save()
    os.remove(caminho)


def migrar_docs_por_ids(model):
    for campo, base_origem in DOCS[model]:
        print('#### Migrando {} de {} ####'.format(campo, model.__name__))

        dir_origem, nome_origem = os.path.split(em_media(base_origem))
        nome_origem = nome_origem.format('(\d+)')
        pat = re.compile('^{}\.\w+$'.format(nome_origem))
        if not os.path.isdir(dir_origem):
            print('  >>> O diretório {} não existe! Abortado.'.format(
                dir_origem))
            continue

        matches = [pat.match(arq) for arq in os.listdir(dir_origem)]
        ids_origens = [(int(m.group(1)),
                        os.path.join(dir_origem, m.group(0)))
                       for m in matches if m]
        objetos = {obj.id: obj for obj in model.objects.all()}
        upload_to = model._meta.get_field(campo).upload_to

        with transaction.atomic():
            for id, origem in ids_origens:
                # associa documento ao objeto
                obj = objetos.get(id)
                if obj:
                    destino = upload_to(obj, os.path.basename(origem))
                    mover_documento(origem, destino)
                    setattr(obj, campo, destino)
                    obj.save()
                else:
                    msg = '  {} (pk={}) não encontrado para documento em [{}]'
                    print(msg.format(model.__name__, id, origem))


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
