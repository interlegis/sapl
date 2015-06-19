from django.db import connection, models

from field_mappings import field_mappings
from migration_base import appconfs, legacy_app

from parlamentares.models import Parlamentar
from django.core.exceptions import ObjectDoesNotExist


def migrate_all(count_limit=None):
    for app in appconfs:
        for model in app.models.values():
            migrate(model, count_limit)


special_transforms = {
    # Field is defined as not null in legacy db, but data includes null values
    #  => transform None to False
    Parlamentar._meta.get_field('unid_deliberativa'): bool,
}


def migrate(model, count_limit=None):

    print 'Migrating %s...' % model.__name__

    # clear all model entries
    model.objects.all().delete()

    def reset_seq(id):
            # resets id sequence
        sql_reset_seq = 'ALTER SEQUENCE %s_id_seq RESTART WITH %s;' % (model._meta.db_table, id)
        cursor = connection.cursor()
        cursor.execute(sql_reset_seq)

    legacy_model = legacy_app.get_model(model.__name__)
    old_pk_name = legacy_model._meta.pk.name
    if old_pk_name == 'id':
        # There is no pk in the legacy table
        reset_seq(1)
        # ...
    else:
        for old in legacy_model.objects.all().order_by(old_pk_name)[:count_limit]:
            old_pk = getattr(old, old_pk_name)
            reset_seq(old_pk)
            new = model()
            for new_field, old_field in field_mappings[model].items():
                value = getattr(old, old_field)
                model_field = model._meta.get_field(new_field)
                transform = special_transforms.get(model_field)
                if transform:
                    value = transform(value)
                else:
                    # check for a relation
                    if isinstance(model_field, models.ForeignKey) and value is not None:
                        try:
                            value = model_field.related_model.objects.get(id=value)
                        except ObjectDoesNotExist:
                            print 'WARNING! FK [%s : %s] not found for value %s (in pk = %s)' % (model.__name__, model_field.name, value, old_pk)
                            value = None
                        else:
                            assert value
                setattr(new, new_field, value)
            new.save()
            assert new.id == old_pk, 'New id is different from old pk!'
