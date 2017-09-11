import os

from decouple import Config, RepositoryEnv
from dj_database_url import parse as db_url

from .settings import *  # flake8: noqa

config = Config(RepositoryEnv(BASE_DIR.child('legacy', '.env')))


INSTALLED_APPS += (
    'sapl.legacy',  # legacy reversed model definitions
)

DATABASES['legacy'] = config('DATABASE_URL', cast=db_url,)

# Sobrescreve o nome dos bancos caso a variável de ambiente seja definida
# Útil para migração em lote de vários bancos
DATABASE_NAME_OVERRIDE = os.environ.get('DATABASE_NAME')
if DATABASE_NAME_OVERRIDE:
    for db in DATABASES.values():
        db['NAME'] = DATABASE_NAME_OVERRIDE

DATABASE_ROUTERS = ['sapl.legacy.router.LegacyRouter', ]

DEBUG = True

MOMMY_CUSTOM_FIELDS_GEN = {
    'django.db.models.ForeignKey': 'sapl.legacy.migration.make_with_log'
}

# delisga indexação fulltext em tempo real
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.BaseSignalProcessor'
