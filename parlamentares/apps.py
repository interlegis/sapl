from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ParlamentaresAppConfig(AppConfig):
    name = 'parlamentares'
    verbose_name = _('Parlamentares')
