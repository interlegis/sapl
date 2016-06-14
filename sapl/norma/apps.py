from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.norma'
    label = 'norma'
    verbose_name = _('Norma Jurídica')
