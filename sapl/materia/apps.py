from django import apps
from sapl.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.materia'
    label = 'materia'
    verbose_name = _('Matéria')

    def ready(self):
        from . import receivers
