from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.audiencia'
    label = 'audiencia'
    verbose_name = _('Audiência Pública')