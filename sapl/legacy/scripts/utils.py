import inspect

from sapl.base.models import Autor
from sapl.legacy.migracao_dados import appconfs


def getsourcelines(model):
    return [line.rstrip('\n').decode('utf-8')
            for line in inspect.getsourcelines(model)[0]]


def get_models_com_referencia_a_autor():

    def tem_referencia_a_autor(model):
        return any(getattr(field, 'related_model', None) == Autor
                   for field in model._meta.get_fields())

    return [model for app in appconfs for model in app.models.values()
            if tem_referencia_a_autor(model)]
