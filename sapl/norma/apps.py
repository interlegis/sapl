from django import apps
from sapl.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.norma'
    label = 'norma'
    verbose_name = _('Norma Jurídica')
