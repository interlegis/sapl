from django import apps
from sapl.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.protocoloadm'
    label = 'protocoloadm'
    verbose_name = _('Protocolo Administrativo')
