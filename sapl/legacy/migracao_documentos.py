import os
import re
from glob import glob
from os.path import join

import yaml
from django.db import transaction
from image_cropping.fields import ImageCropField

from sapl.base.models import CasaLegislativa
from sapl.legacy.migracao_dados import exec_legado
from sapl.materia.models import (DocumentoAcessorio, MateriaLegislativa,
                                 Proposicao)
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import (DocumentoAcessorioAdministrativo,
                                      DocumentoAdministrativo)
from sapl.sessao.models import SessaoPlenaria

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

DOCS = {model: [(campo, join('sapl_documentos', origem))
                for campo, origem, in campos]
        for model, campos in DOCS.items()}


def mover_documento(repo, origem, destino):
    origem, destino = [join(repo.working_dir, c) if not os.path.isabs(c) else c
                       for c in (origem, destino)]
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    repo.git.mv(origem, destino)


def migrar_logotipo(repo, casa, propriedades):
    print('.... Migrando logotipo da casa ....')
    [(campo, origem)] = DOCS[CasaLegislativa]
    # a extensão do logo pode ter sido ajustada pelo tipo real do arquivo
    nome_nas_propriedades = os.path.splitext(propriedades['id_logo'])[0]
    arquivos = glob(join(repo.working_dir, origem.format(nome_nas_propriedades)))
    if arquivos:
        assert len(arquivos) == 1, 'Há mais de um logotipo para a casa'
        [logo] = arquivos
        destino = join(CasaLegislativa._meta.get_field(campo).upload_to,
                       os.path.basename(logo))
        mover_documento(repo, logo, destino)
        casa.logotipo = destino


def migrar_propriedades_da_casa(repo):
    print('#### Migrando propriedades da casa ####')
    caminho = join(repo.working_dir, 'sapl_documentos/propriedades.yaml')
    repo.git.execute('git annex get'.split() + [caminho])
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

    # localidade
    sql_localidade = '''
        select nom_localidade, sgl_uf from localidade
        where cod_localidade = {}'''.format(propriedades['cod_localidade'])
    [(casa.municipio, casa.uf)] = exec_legado(sql_localidade)

    # logotipo
    migrar_logotipo(repo, casa, propriedades)

    casa.save()
    repo.git.rm(caminho)


def migrar_docs_por_ids(repo, model):
    for campo, base_origem in DOCS[model]:
        print('#### Migrando {} de {} ####'.format(campo, model.__name__))

        dir_origem, nome_origem = os.path.split(
            join(repo.working_dir, base_origem))
        nome_origem = nome_origem.format('(\d+)')
        pat = re.compile('^{}\.\w+$'.format(nome_origem))
        if not os.path.isdir(dir_origem):
            print('  >>> O diretório {} não existe! Abortado.'.format(
                dir_origem))
            continue

        matches = [pat.match(arq) for arq in os.listdir(dir_origem)]
        ids_origens = [(int(m.group(1)),
                        join(dir_origem, m.group(0)))
                       for m in matches if m]
        objetos = {obj.id: obj for obj in model.objects.all()}
        upload_to = model._meta.get_field(campo).upload_to
        tem_cropping = isinstance(model._meta.get_field(campo), ImageCropField)

        with transaction.atomic():
            for id, origem in ids_origens:
                # associa documento ao objeto
                obj = objetos.get(id)
                if obj:
                    destino = upload_to(obj, os.path.basename(origem))
                    mover_documento(repo, origem, destino)
                    setattr(obj, campo, destino)
                    if tem_cropping:
                        # conserta link do git annex (antes do commit)
                        # pois o conteúdo das imagens é acessado pelo cropping
                        repo.git.execute('git annex fix'.split() + [destino])
                    obj.save()
                else:
                    msg = '  {} (pk={}) não encontrado para documento em [{}]'
                    print(msg.format(model.__name__, id, origem))


def migrar_documentos(repo):
    # aqui supomos que as pastas XSLT e sapl_documentos estão em
    # <repo.working_dir> com o conteúdo exportado do zope
    # Os arquivos das pastas serão (git) MOVIDOS para a nova estrutura!
    #
    # Isto significa que para rodar novamente esta função é preciso
    # restaurar o repo ao estado anterior

    mover_documento(repo, 'XSLT', 'sapl/public/XSLT')

    migrar_propriedades_da_casa(repo)

    # garante que o conteúdo das fotos dos parlamentares esteja presente
    # (necessário para o cropping de imagem)
    repo.git.execute('git annex get sapl_documentos/parlamentar'.split())

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
        migrar_docs_por_ids(repo, model)

    sobrando = [join(dir, file)
                for (dir, _, files) in os.walk(join(repo.working_dir,
                                                    'sapl_documentos'))
                for file in files]
    if sobrando:
        print('\n#### Encerrado ####\n\n'
              '{} documentos sobraram sem ser migrados!!!'.format(
                  len(sobrando)))
