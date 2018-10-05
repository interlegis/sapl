import os

from decouple import Config, RepositoryEnv
from dj_database_url import parse as db_url

from sapl.legacy.scripts.exporta_zope.variaveis_comuns import \
    DIR_DADOS_MIGRACAO

from .settings import *  # flake8: noqa

config = Config(RepositoryEnv(BASE_DIR.child('legacy', '.env')))


INSTALLED_APPS += (
    'sapl.legacy',  # legacy reversed model definitions
)

DATABASES['legacy'] = config('DATABASE_URL_FONTE', cast=db_url,)
DATABASES['default'] = config(
    'DATABASE_URL_DESTINO',
    cast=lambda v: v if isinstance(v, dict) else db_url(v),
    default=DATABASES['default'])

# Sobrescreve o nome dos bancos caso a variável de ambiente seja definida
# Útil para migração em lote de vários bancos
DATABASE_NAME_OVERRIDE = os.environ.get('DATABASE_NAME')
if DATABASE_NAME_OVERRIDE:
    DATABASES['legacy']['NAME'] = DATABASE_NAME_OVERRIDE
    # não altera o nome se o destino é um banco em memória
    if not DATABASES['default']['NAME'] == ':memory:':
        DATABASES['default']['NAME'] = DATABASE_NAME_OVERRIDE

DATABASE_ROUTERS = ['sapl.legacy.router.LegacyRouter', ]

DEBUG = True

# delisga indexação fulltext em tempo real
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.BaseSignalProcessor'

SHELL_PLUS_DONT_LOAD = ['legacy']

NOME_BANCO_LEGADO = DATABASES['legacy']['NAME']
DIR_REPO = Path(DIR_DADOS_MIGRACAO, 'repos', NOME_BANCO_LEGADO)

MEDIA_ROOT = DIR_REPO
