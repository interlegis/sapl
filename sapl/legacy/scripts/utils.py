import inspect

from sapl.base.models import Autor
from sapl.legacy.migracao_dados import appconfs


def get_models_com_referencia_a(apontado):

    def tem_referencia_a_apontado(model):
        return any(getattr(field, 'related_model', None) == apontado
                   for field in model._meta.get_fields())

    return [model for app in appconfs for model in app.models.values()
            if tem_referencia_a_apontado(model)]
