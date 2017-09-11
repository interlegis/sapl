import os

from decouple import Config, RepositoryEnv
from dj_database_url import parse as db_url

from .settings import *  # flake8: noqa

config = Config(RepositoryEnv(BASE_DIR.child('legacy', '.env')))


INSTALLED_APPS += (
    'sapl.legacy',  # legacy reversed model definitions
)

DATABASES['legacy'] = config('DATABASE_URL_FONTE', cast=db_url,)
DATABASES['default'] = config('DATABASE_URL_DESTINO', cast=db_url,
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

MOMMY_CUSTOM_FIELDS_GEN = {
    'django.db.models.ForeignKey': 'sapl.legacy.migration.make_with_log'
}

# delisga indexação fulltext em tempo real
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.BaseSignalProcessor'
