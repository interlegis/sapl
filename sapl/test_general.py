"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
import pytest
from django.apps import apps
from model_mommy import mommy

from .settings import SAPL_APPS

pytestmark = pytest.mark.django_db


def test_str_sanity():
    # this simply a sanity check
    # __str__ semantics is not considered and should be tested separetely
    sapl_appconfs = [apps.get_app_config(n) for n in SAPL_APPS]
    for app in sapl_appconfs:
        for model in app.get_models():
            obj = mommy.prepare(model)
            try:
                str(obj)
            except Exception as exc:
                msg = '%s.%s.__str__ is broken.' % (
                    model.__module__, model.__name__)
                raise AssertionError(msg, exc)
