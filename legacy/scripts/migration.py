from django.apps.config import AppConfig
from django.core.exceptions import ObjectDoesNotExist
from django.db import connections, models
from django.db.models.base import ModelBase
from model_mommy import mommy

from field_renames import field_renames
from migration_base import legacy_app, appconfs
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


def migrate(obj=appconfs, count_limit=None):
    # warning: model/app migration order is of utmost importance

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


def exec_sql(sql, db='default'):
    cursor = connections[db].cursor()
    cursor.execute(sql)
    return cursor


def iter_sql_records(sql, db):
    class Record(object):
        pass
    cursor = exec_sql(sql, db)
    fieldnames = [name[0] for name in cursor.description]
    for row in cursor.fetchall():
        record = Record()
        record.__dict__.update(zip(fieldnames, row))
        yield record


def save_with_id(new, id):
    sequence_name = '%s_id_seq' % type(new)._meta.db_table
    cursor = exec_sql('SELECT last_value from %s;' % sequence_name)
    (last_value,) = cursor.fetchone()
    if last_value == 1 or id != last_value + 1:
        # we explicitly set the next id if last_value == 1
        # because last_value == 1 for a table containing either 0 or 1 records
        # (we would have trouble for id == 2 and a missing id == 1)
        exec_sql('ALTER SEQUENCE %s RESTART WITH %s;' % (sequence_name, id))
    new.save()
    assert new.id == id, 'New id is different from provided!'


def make_stub(model, id):
    new = mommy.prepare(model)
    save_with_id(new, id)
    return new


def migrate_model(model, to_delete, count_limit=None):

    print 'Migrating %s...' % model.__name__

    # clear all model entries
    model.objects.all().delete()

    legacy_model = legacy_app.get_model(model.__name__)
    old_pk_name = legacy_model._meta.pk.name

    # setup migration strategy for tables with or without a pk
    if old_pk_name == 'id':
        # There is no pk in the legacy table

        def get_old_pk(old):
            return '-- WITHOUT PK --'

        def save(new, id):
            new.save()

        old_records = iter_sql_records(
            'select * from ' + legacy_model._meta.db_table, 'legacy')
    else:
        def get_old_pk(old):
            return getattr(old, old_pk_name)
        save = save_with_id
        old_records = legacy_model.objects.all().order_by(old_pk_name)[:count_limit]

    # convert old records to new ones
    for old in old_records:
        old_pk = get_old_pk(old)
        new = model()
        for new_field, old_field in field_renames[model].items():
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
                        msg = 'FK [%s (%s) : %s] not found for value %s' % (
                            model.__name__, old_pk, model_field.name, value)
                        if value == 0:
                            # we interpret FK == 0 as actually FK == NONE
                            value = None
                            warn(msg + ' => NONE for zero value')
                        else:
                            value = make_stub(model_field.related_model, value)
                            warn(msg + ' => STUB CREATED')
                    else:
                        assert value
            setattr(new, new_field, value)
        save(new, old_pk)
        if getattr(old, 'ind_excluido', False):
            to_delete.append(new)


def get_ind_excluido(obj):
    legacy_model = legacy_app.get_model(type(obj).__name__)
    return getattr(legacy_model.objects.get(**{legacy_model._meta.pk.name: obj.id}), 'ind_excluido', False)


def check_app_no_ind_excluido(app):
    for model in app.models.values():
        assert not any(get_ind_excluido(obj) for obj in model.objects.all())
    print 'OK!'
