"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class MateriaAppConfig(AppConfig):
    name = 'materia'
    verbose_name = _('Matéria')
