from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'protocoloadm'
    verbose_name = _('Protocolo Administrativo')
