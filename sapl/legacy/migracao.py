import subprocess
import tarfile

from django.conf import settings

from sapl.legacy.migracao_dados import migrar_dados
from sapl.legacy.migracao_documentos import migrar_documentos
from sapl.legacy.migracao_usuarios import migrar_usuarios


def migrar(interativo=False):
    migrar_dados(interativo=interativo)
    migrar_usuarios()
    migrar_documentos()


# fonte: https://stackoverflow.com/a/17081026/1877490
def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


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
