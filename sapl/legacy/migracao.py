from sapl.legacy.migracao_dados import migrar_dados
from sapl.legacy.migracao_documentos import migrar_documentos
from sapl.legacy.migracao_usuarios import migrar_usuarios


def migrar(interativo=False):
    migrar_dados(interativo)
    migrar_usuarios()
    migrar_documentos()
