from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.videoconf'
    label = 'videoconf'
    verbose_name = _('Video-conferência')