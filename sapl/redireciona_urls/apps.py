from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.redireciona_urls'
    label = 'redireciona_urls'
    verbose_name = _('Redirecionador de URLs')
