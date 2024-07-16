from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.sessao'
    label = 'sessao'
    verbose_name = _('Sessão Plenária')
