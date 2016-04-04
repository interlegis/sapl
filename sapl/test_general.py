import pytest
from django.db.models import CharField, TextField
from django.apps import apps
from model_mommy import mommy

from .settings import SAPL_APPS

pytestmark = pytest.mark.django_db


def test_charfiled_textfield():
    for model in apps.get_models():
        fields = model._meta.local_fields
        for field in fields:
                if isinstance(field, (CharField, TextField)):
                    msg = 'Model = %s || Field = %s - %s - %s' % (
                           model.__name__,
                           field.attname,
                           type(field).__name__,
                           field.null)
                    raise AssertionError(msg)


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
