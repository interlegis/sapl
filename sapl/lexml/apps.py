from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.lexml'
    label = 'lexml'
    verbose_name = _('LexML')
