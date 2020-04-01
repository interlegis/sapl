from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.sdr'
    label = 'sdr'
    verbose_name = _('Sistema de Deliberação Remota')