from django import apps
from sapl.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.relatorios'
    label = 'relatorios'
    verbose_name = _('Relatórios')
