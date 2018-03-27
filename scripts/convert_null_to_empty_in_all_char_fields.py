from django.apps import apps
from django.db import models

from sapl.settings import SAPL_APPS


def convert_null_to_empty():
    for name in SAPL_APPS:
        for model in apps.get_app_config(name).get_models():
            try:
                print('Convertendo null p/ vazio. model [%s]'
                      % model._meta.model_name)
                char_fields = [f for f in model._meta.fields
                               if isinstance(f, (models.CharField,
                                                 models.TextField))]
                for obj in model.objects.all():
                    for field in char_fields:
                        if getattr(obj, field.name) is None:
                            setattr(obj, field.name, '')
                    obj.save()
            except Exception as e:
                print(e)
