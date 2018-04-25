import subprocess

from sapl.legacy.migracao_dados import (REPO, TAG_MARCO, gravar_marco, info,
                                        migrar_dados)
from sapl.legacy.migracao_documentos import migrar_documentos
from sapl.legacy.migracao_usuarios import migrar_usuarios
from sapl.legacy.scripts.exporta_zope.variaveis_comuns import TAG_ZOPE
from sapl.legacy_migration_settings import DIR_REPO, NOME_BANCO_LEGADO


def adornar_msg(msg):
    return '\n{1}\n{0}\n{1}'.format(msg, '#' * len(msg))


def migrar(interativo=False):
    if TAG_MARCO in REPO.tags:
        info('A migração já está feita.')
        return
    assert TAG_ZOPE in REPO.tags, adornar_msg(
        'Antes de migrar '
        'é necessário fazer a exportação de documentos do zope')
    migrar_dados(interativo=interativo)
    migrar_usuarios(REPO.working_dir)
    migrar_documentos(REPO)
    gravar_marco()
    gerar_pacote()


def gerar_pacote():

    # backup do banco
    print('Gerando backup do banco... ', end='', flush=True)
    arq_backup = DIR_REPO.child('{}.backup'.format(NOME_BANCO_LEGADO))
    backup_cmd = '''
        pg_dump --host localhost --port 5432 --username postgres --no-password
        --format custom --blobs --verbose --file {} {}'''.format(
        arq_backup, NOME_BANCO_LEGADO)
    subprocess.check_output(backup_cmd.split(), stderr=subprocess.DEVNULL)
    print('SUCESSO')

    # tar de media/sapl
    print('Criando tar de media... ', end='', flush=True)
    arq_tar = DIR_REPO.child('{}.media.tar'.format(NOME_BANCO_LEGADO))
    subprocess.check_output(['tar', 'cfh', arq_tar, '-C', DIR_REPO, 'sapl'])
    print('SUCESSO')
