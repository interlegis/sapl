import pytest
from model_mommy import mommy

from .utils import sapl_appconfs

pytestmark = pytest.mark.django_db


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
                raise AssertionError(msg, exc) from exc
