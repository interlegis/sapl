from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sessao'
    verbose_name = _('Sessão Plenária')
