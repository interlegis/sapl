from django.apps.config import AppConfig
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, models
from django.db.models.base import ModelBase

from field_mappings import field_mappings
from migration_base import legacy_app
from parlamentares.models import Parlamentar


def info(msg):
    print 'INFO: ' + msg


def warn(msg):
    print 'WARNING! ' + msg

special_transforms = {}


def special(model, fieldname):
    def wrap(function):
        special_transforms[model._meta.get_field(fieldname)] = function
        return function
    return wrap


@special(Parlamentar, 'unid_deliberativa')
def none_to_false(value):
    # Field is defined as not null in legacy db, but data includes null values
    #  => transform None to False
    if value is None:
        warn('null converted to False')
    return bool(value)


def migrate(obj, count_limit=None):
    to_delete = []
    _do_migrate(obj, to_delete, count_limit)
    # exclude logically deleted in legacy base
    info('Deleting models with ind_excluido...')
    for obj in to_delete:
        obj.delete()


def _do_migrate(obj, to_delete, count_limit=None):
    if isinstance(obj, AppConfig):
        _do_migrate(obj.models.values(), to_delete, count_limit)
    elif isinstance(obj, ModelBase):
        migrate_model(obj, to_delete, count_limit)
    elif hasattr(obj, '__iter__'):
        for item in obj:
            _do_migrate(item, to_delete, count_limit)
    else:
        raise TypeError('Parameter must be a Model, AppConfig or a sequence of them')


def migrate_model(model, to_delete, count_limit=None):

    print 'Migrating %s...' % model.__name__

    # clear all model entries
    model.objects.all().delete()

    def reset_seq(id):
        # resets id sequence
        if id > reset_seq.last_id + 1:
            sql_reset_seq = 'ALTER SEQUENCE %s_id_seq RESTART WITH %s;' % (model._meta.db_table, id)
            cursor = connection.cursor()
            cursor.execute(sql_reset_seq)
        reset_seq.last_id = id
    reset_seq.last_id = -1

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
                            warn('FK [%s : %s] not found for value %s (in pk = %s)' % (
                                model.__name__, model_field.name, value, old_pk))
                            value = None
                        else:
                            assert value
                setattr(new, new_field, value)
            new.save()
            assert new.id == old_pk, 'New id is different from old pk!'
            if getattr(old, 'ind_excluido', False):
                to_delete.append(new)


def get_ind_excluido(obj):
    legacy_model = legacy_app.get_model(type(obj).__name__)
    return getattr(legacy_model.objects.get(**{legacy_model._meta.pk.name: obj.id}), 'ind_excluido', False)


def check_app_no_ind_excluido(app):
    for model in app.models.values():
        assert not any(get_ind_excluido(obj) for obj in model.objects.all())
    print 'OK!'
