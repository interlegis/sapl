import os

from decouple import AutoConfig, Config, RepositoryEnv
from dj_database_url import parse as db_url

from .settings import *  # flake8: noqa

config = AutoConfig()
config.config = Config(RepositoryEnv(os.path.abspath('sapl/legacy/.env')))


INSTALLED_APPS += (
    'sapl.legacy',  # legacy reversed model definitions
)

DATABASES['legacy'] = config('DATABASE_URL', cast=db_url,)

DATABASE_ROUTERS = ['sapl.legacy.router.LegacyRouter', ]

DEBUG = False

MOMMY_CUSTOM_FIELDS_GEN = {
    'django.db.models.ForeignKey': 'sapl.legacy.migration.make_with_log'
}
