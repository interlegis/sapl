
import django
from django.utils.translation import ugettext_lazy as _


class AppConfig(django.apps.AppConfig):
    name = 'sapl.base'
    label = 'base'
    verbose_name = _('Dados Básicos')
