import os

from decouple import Config, RepositoryEnv, AutoConfig
from dj_database_url import parse as db_url

from .settings import *  # flake8: noqa


config = AutoConfig()
config.config = Config(RepositoryEnv(os.path.abspath('sapl/legacy/.env')))


INSTALLED_APPS += (
    'sapl.legacy',  # legacy reversed model definitions
)

DATABASES['legacy'] = config('DATABASE_URL', cast=db_url,)

"""DATABASES['legacy'] = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'legacy_interlegis',
    'USER': 'root',
    'PASSWORD': '',
    'HOST': '',   # Or an IP Address that your DB is hosted on
    'PORT': '3306',
}
"""

DATABASE_ROUTERS = ['sapl.legacy.router.LegacyRouter', ]

DEBUG = False

MOMMY_CUSTOM_FIELDS_GEN = {
    'django.db.models.ForeignKey': 'sapl.legacy.migration.make_with_log'
}
