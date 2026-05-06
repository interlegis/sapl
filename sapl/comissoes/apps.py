from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.comissoes'
    label = 'comissoes'
    verbose_name = _('Comissões')
