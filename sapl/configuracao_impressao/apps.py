from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.configuracao_impressao'
    label = 'configuracao_impressao'
    verbose_name = _('Configuração de Impressão')
