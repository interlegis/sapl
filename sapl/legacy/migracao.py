import subprocess
from getpass import getpass

import requests
from django.core import management
from unipath import Path

from sapl.legacy.migracao_dados import (REPO, TAG_MARCO, gravar_marco, info,
                                        migrar_dados)
from sapl.legacy.migracao_documentos import migrar_documentos
from sapl.legacy.migracao_usuarios import migrar_usuarios
from sapl.legacy.scripts.exporta_zope.variaveis_comuns import TAG_ZOPE
from sapl.legacy_migration_settings import DIR_REPO, NOME_BANCO_LEGADO
from sapl.materia.models import Proposicao


def adornar_msg(msg):
    return '\n{1}\n{0}\n{1}'.format(msg, '#' * len(msg))


def migrar(apagar_do_legado=False):
    if TAG_MARCO in REPO.tags:
        info('A migração já está feita.')
        return
    assert TAG_ZOPE in REPO.tags, adornar_msg(
        'Antes de migrar '
        'é necessário fazer a exportação de documentos do zope')
    management.call_command('migrate')
    migrar_dados(apagar_do_legado)
    migrar_usuarios(REPO.working_dir)
    migrar_documentos(REPO)
    gravar_marco()
    # compactar_media()


def compactar_media():

    # tar de media/sapl
    print('Criando tar de media... ', end='', flush=True)
    arq_tar = DIR_REPO.child('{}.media.tar'.format(NOME_BANCO_LEGADO))
    arq_tar.remove()
    subprocess.check_output(['tar', 'cfh', arq_tar, '-C', DIR_REPO, 'sapl'])
    print('SUCESSO')


PROPOSICAO_UPLOAD_TO = Proposicao._meta.get_field('texto_original').upload_to


def salva_conteudo_do_sde(proposicao, conteudo):
    caminho_relativo = PROPOSICAO_UPLOAD_TO(
        proposicao, 'proposicao_sde_{}.xml'.format(proposicao.pk))
    caminho_absoluto = Path(REPO.working_dir, caminho_relativo)
    caminho_absoluto.parent.mkdir(parents=True)
    # ajusta caminhos para folhas de estilo
    conteudo = conteudo.replace(b'"XSLT/HTML', b'"/XSLT/HTML')
    conteudo = conteudo.replace(b"'XSLT/HTML", b"'/XSLT/HTML")
    with open(caminho_absoluto, 'wb') as arq:
        arq.write(conteudo)
    proposicao.texto_original = caminho_relativo
    proposicao.save()


def scrap_sde(url, usuario, senha=None):
    if not senha:
        senha = getpass()

    # login
    session = requests.session()
    res = session.post('{}?retry=1'.format(url),
                       {'__ac_name': usuario, '__ac_password': senha})
    assert res.status_code == 200

    url_proposicao = '{}/sapl_documentos/proposicao/{}/renderXML?xsl=__default__'  # noqa
    total = Proposicao.objects.count()
    for num, proposicao in enumerate(Proposicao.objects.all()):
        pk = proposicao.pk
        res = session.get(url_proposicao.format(url, pk))
        print("pk: {} status: {} (progresso: {:.2%})".format(
            pk, res.status_code, num / total))
        if res.status_code == 200:
            salva_conteudo_do_sde(proposicao, res.content)
