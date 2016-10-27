
from django.utils.translation import ugettext_lazy as _
import django


class AppConfig(django.apps.AppConfig):
    name = 'sapl.base'
    label = 'base'
    verbose_name = _('Dados Básicos')
