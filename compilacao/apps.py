from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'compilacao'
    verbose_name = _('Compilação')
