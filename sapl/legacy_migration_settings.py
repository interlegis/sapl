# Settings for data migration from mysql legacy to new postgres database

from .settings import *

INSTALLED_APPS += (
    'legacy',  # legacy reversed model definitions
)

DATABASES['legacy'] = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'sapl25',
    'USER': 'root',
    'PASSWORD': 'admin',
    'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
    'PORT': '3306',
}

DATABASE_ROUTERS = ['legacy.router.LegacyRouter', ]
