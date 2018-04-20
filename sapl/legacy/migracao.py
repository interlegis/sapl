import subprocess
import tarfile

from django.conf import settings

from sapl.legacy.migracao_dados import REPO, gravar_marco, migrar_dados
from sapl.legacy.migracao_documentos import migrar_documentos
from sapl.legacy.migracao_usuarios import migrar_usuarios
from sapl.legacy.scripts.exporta_zope.variaveis_comuns import TAG_ZOPE


def adornar_msg(msg):
    return '\n{1}\n{0}\n{1}'.format(msg, '#' * len(msg))


def migrar(interativo=False):
    assert TAG_ZOPE in {t.name for t in REPO.tags}, adornar_msg(
        'Antes de migrar '
        'é necessário fazer a exportação de documentos do zope')
    migrar_dados(interativo=interativo)
    migrar_usuarios(REPO.working_dir)
    migrar_documentos(REPO)
    gravar_marco()


def gerar_pacote():
    banco = settings.DATABASES['legacy']['NAME']

    # backup do banco
    print('Gerando backup do banco... ', end='', flush=True)
    arq_backup = settings.MEDIA_ROOT.child('{}.backup'.format(banco))
    backup_cmd = '''
        pg_dump --host localhost --port 5432 --username postgres --no-password
        --format custom --blobs --verbose --file {} {}'''.format(
        arq_backup, banco)
    subprocess.check_output(backup_cmd.split(), stderr=subprocess.DEVNULL)
    print('SUCESSO')

    # tar de media/sapl
    print('Criando tar de media... ', end='', flush=True)
    tar_media = settings.MEDIA_ROOT.child('{}.media.tgz'.format(banco))
    dir_media = settings.MEDIA_ROOT.child('sapl')
    with tarfile.open(tar_media, "w:gz") as tar:
        tar.add(dir_media, arcname=dir_media.name)
    print('SUCESSO')
