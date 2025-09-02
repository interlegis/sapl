from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = "sapl.materia"
    label = "materia"
    verbose_name = _("Matéria")
