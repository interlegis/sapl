DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.messages',
    'crud_tests',
    'crispy_forms',
)

ROOT_URLCONF = 'crud_tests.urls'

USE_TZ = True

SECRET_KEY = 'zzz...'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
}]

SILENCED_SYSTEM_CHECKS = [
    '1_7.W001',  # Unset MIDDLEWARE_CLASSES warning
]


TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = False
USE_TZ = True
# DATE_FORMAT = 'N j, Y'
DATE_FORMAT = 'd/m/Y'
SHORT_DATE_FORMAT = 'd/m/Y'
DATE_INPUT_FORMATS = ('%d/%m/%Y', '%m-%d-%Y', '%Y-%m-%d')
