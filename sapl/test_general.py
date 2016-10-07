import pytest
from django.apps import apps
from django.db.models import CharField, TextField
from model_mommy import mommy

from .settings import SAPL_APPS

pytestmark = pytest.mark.django_db

sapl_appconfs = [apps.get_app_config(n[5:]) for n in SAPL_APPS]


def test_charfield_textfield():
    for app in sapl_appconfs:
        for model in app.get_models():
            fields = model._meta.local_fields
            for field in fields:
                if isinstance(field, (CharField, TextField)):
                    assert not field.null, 'This %s is null: %s.%s' % (
                        type(field).__name__,
                        model.__name__,
                        field.attname)


def test_str_sanity():
    # this simply a sanity check
    # __str__ semantics is not considered and should be tested separetely
    for app in sapl_appconfs:
        for model in app.get_models():
            obj = mommy.prepare(model)
            try:
                str(obj)
            except Exception as exc:
                msg = '%s.%s.__str__ is broken.' % (
                    model.__module__, model.__name__)
                raise AssertionError(msg, exc)
