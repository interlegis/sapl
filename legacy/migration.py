import re

import pkg_resources
import yaml
from django.apps import apps
from django.apps.config import AppConfig
from django.core.exceptions import ObjectDoesNotExist
from django.db import connections, models
from django.db.models.base import ModelBase
from model_mommy import mommy

from comissoes.models import Composicao, Participacao
from parlamentares.models import Parlamentar


# BASE ######################################################################

# this order is important for the migration
appconfs = [apps.get_app_config(n) for n in [
    'parlamentares',
    'comissoes',
    'materia',
    'norma',
    'sessao',
    'lexml',
    'protocoloadm', ]]
name_sets = [set(m.__name__ for m in ac.get_models()) for ac in appconfs]

# apps do not overlap
for s1 in name_sets:
    for s2 in name_sets:
        if s1 is not s2:
            assert not s1.intersection(s2)

# apps include all legacy models
legacy_app = apps.get_app_config('legacy')
legacy_model_names = set(m.__name__ for m in legacy_app.get_models())

model_dict = {m.__name__: m for ac in appconfs for m in ac.get_models()}


# RENAMES ###################################################################

MODEL_RENAME_PATTERN = re.compile('(.+) \((.+)\)')


def get_renames():
    field_renames = {}
    model_renames = {}
    for app in appconfs:
        app_rename_data = yaml.load(pkg_resources.resource_string(app.module.__name__, 'legacy.yaml'))
        for model_name, renames in app_rename_data.items():
            match = MODEL_RENAME_PATTERN.match(model_name)
            if match:
                model_name, old_name = match.groups()
            else:
                old_name = None
            model = getattr(app.models_module, model_name)
            if old_name:
                model_renames[model] = old_name
            field_renames[model] = renames

    # collect renames from parent classes
    for model, renames in field_renames.items():
        if any(parent in field_renames for parent in model.__mro__[1:]):
            renames = {}
            for parent in reversed(model.__mro__):
                if parent in field_renames:
                    renames.update(field_renames[parent])
            field_renames[model] = renames

    # remove abstract classes
    for model in field_renames:
        if model._meta.abstract:
            del field_renames[model]

    return field_renames, model_renames


# MIGRATION #################################################################

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


@special(Parlamentar, 'unidade_deliberativa')
def none_to_false(obj, value):
    # Field is defined as not null in legacy db, but data includes null values
    #  => transform None to False
    if value is None:
        warn('null converted to False')
    return bool(value)


@special(Participacao, 'composicao')
def get_participacao_composicao(obj, value):
    # value parameter is ignored
    new = Composicao()
    for new_field, value in [('comissao', obj.cod_comissao),
                             ('periodo', obj.cod_periodo_comp)]:
        model_field = Composicao._meta.get_field(new_field)
        value = get_related_if_foreignkey(model_field, '???', value)
        setattr(new, new_field, value)
    previous = Composicao.objects.filter(comissao=new.comissao, periodo=new.periodo)
    if previous:
        assert len(previous) == 1
        return previous[0]
    else:
        new.save()
        return new


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

    legacy_model_name = model_renames.get(model, model.__name__)
    if legacy_model_name.upper() == 'IGNORE':
        print 'Model ignored: %s' % model.__name__
        return

    print 'Migrating %s...' % model.__name__

    # clear all model entries
    model.objects.all().delete()

    legacy_model = legacy_app.get_model(legacy_model_name)
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
                value = transform(old, value)
            else:
                # check for a relation
                value = get_related_if_foreignkey(model_field, old_pk, value)
            setattr(new, new_field, value)
        save(new, old_pk)
        if getattr(old, 'ind_excluido', False):
            to_delete.append(new)


def get_related_if_foreignkey(model_field, old_pk, value):
    if isinstance(model_field, models.ForeignKey) and value is not None:
        try:
            value = model_field.related_model.objects.get(id=value)
        except ObjectDoesNotExist:
            msg = 'FK [%s (%s) : %s] not found for value %s' % (
                model_field.model.__name__, old_pk, model_field.name, value)
            if value == 0:
                # we interpret FK == 0 as actually FK == NONE
                value = None
                warn(msg + ' => NONE for zero value')
            else:
                value = make_stub(model_field.related_model, value)
                warn(msg + ' => STUB CREATED')
        else:
            assert value
    return value


def get_ind_excluido(obj):
    legacy_model = legacy_app.get_model(type(obj).__name__)
    return getattr(legacy_model.objects.get(**{legacy_model._meta.pk.name: obj.id}), 'ind_excluido', False)


def check_app_no_ind_excluido(app):
    for model in app.models.values():
        assert not any(get_ind_excluido(obj) for obj in model.objects.all())
    print 'OK!'
