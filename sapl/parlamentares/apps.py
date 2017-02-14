from django import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.parlamentares'
    label = 'parlamentares'
    verbose_name = _('Parlamentares')
