import django
from django.utils.translation import gettext_lazy as _


class AppConfig(django.apps.AppConfig):
    name = 'sapl.base'
    label = 'base'
    verbose_name = _('Dados Básicos')

    def ready(self):
        from sapl.base import receivers
