from django.db import models

from sapl.utils import appconfs


def convert_null_to_empty():
    for app in appconfs:
        for model in app.get_models():
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
