from django.db import connection, models

from field_mappings import field_mappings
from migration_base import appconfs, legacy_app


def migrate_all():
    for app in appconfs:
        for model in app.models.values():
            migrate(model)


def migrate(model):

        print 'Migrating %s...' % model.__name__

        # clear all model entries
        model.objects.all().delete()
        # resets id sequence
        sql_reset_seq = 'ALTER SEQUENCE %s_id_seq RESTART WITH 1;' % model._meta.db_table
        cursor = connection.cursor()
        cursor.execute(sql_reset_seq)

        legacy_model = legacy_app.get_model(model.__name__)
        old_pk_name = legacy_model._meta.pk.name
        if old_pk_name == 'id':
            # There is no pk in the legacy table
            pass
        else:
            for old in legacy_model.objects.all().order_by(old_pk_name):
                old_pk = getattr(old, old_pk_name)
                new = model()
                while not new.id:
                    for new_field, old_field in field_mappings[model].items():
                        value = getattr(old, old_field)
                        # check for a relation
                        model_field = model._meta.get_field(new_field)
                        # TODO ... test for special transformations first (e.g. Parlamentar.localidade_residencia)
                        # elfi ...
                        if isinstance(model_field, models.ForeignKey):
                            value = model_field.related_model.objects.get(id=value)
                            assert value
                        setattr(new, new_field, value)
                    new.save()
                    assert new.id <= old_pk, 'New id exceeds old pk!'
                    if new.id < old_pk:
                        new.delete()
                        new = model()
