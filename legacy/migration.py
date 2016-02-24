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
from sessao.models import SessaoPlenaria

# BASE ######################################################################

#  apps to be migrated, in app dependency order (very important)
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
        app_rename_data = yaml.load(
            pkg_resources.resource_string(app.module.__name__, 'legacy.yaml'))
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
    field_renames = {m: r for m, r in field_renames.items()
                     if not m._meta.abstract}

    return field_renames, model_renames


# MIGRATION #################################################################

def info(msg):
    print('INFO: ' + msg)


def warn(msg):
    print('WARNING! ' + msg)


def get_fk_related(field, value, label=None):
    if value is not None:
        try:
            value = field.related_model.objects.get(id=value)
        except ObjectDoesNotExist:
            msg = 'FK [%s] not found for value %s ' \
                '(in %s %s)' % (
                    field.name, value,
                    field.model.__name__, label or '---')
            if value == 0:
                # we interpret FK == 0 as actually FK == NONE
                value = None
                warn(msg + ' => using NONE for zero value')
            else:
                value = make_stub(field.related_model, value)
                warn(msg + ' => STUB CREATED')
        else:
            assert value
    return value


def get_field(model, fieldname):
    return model._meta.get_field(fieldname)


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


class DataMigrator(object):

    def __init__(self):
        self.field_renames, self.model_renames = get_renames()

    def populate_renamed_fields(self, new, old):
        renames = self.field_renames[type(new)]

        for field in new._meta.fields:
            old_field_name = renames.get(field.name)
            if old_field_name:
                old_value = getattr(old, old_field_name)
                if isinstance(field, models.ForeignKey):
                    old_type = type(old)  # not necessarily a model
                    if hasattr(old_type, '_meta') and \
                            old_type._meta.pk.name != 'id':
                        label = old.pk
                    else:
                        label = '-- WITHOUT PK --'
                    value = get_fk_related(field, old_value, label)
                else:
                    value = getattr(old, old_field_name)
                setattr(new, field.name, value)

    def migrate(self, obj=appconfs):
        # warning: model/app migration order is of utmost importance

        self.to_delete = []
        info('Starting %s migration...' % obj)
        self._do_migrate(obj)
        # exclude logically deleted in legacy base
        info('Deleting models with ind_excluido...')
        for obj in self.to_delete:
            obj.delete()

    def _do_migrate(self, obj):
        if isinstance(obj, AppConfig):
            models_to_migrate = (model for model in obj.models.values()
                                 if model in self.field_renames)
            self._do_migrate(models_to_migrate)
        elif isinstance(obj, ModelBase):
            self.migrate_model(obj)
        elif hasattr(obj, '__iter__'):
            for item in obj:
                self._do_migrate(item)
        else:
            raise TypeError(
                'Parameter must be a Model, AppConfig or a sequence of them')

    def migrate_model(self, model):
        print('Migrating %s...' % model.__name__)

        legacy_model_name = self.model_renames.get(model, model.__name__)
        legacy_model = legacy_app.get_model(legacy_model_name)
        legacy_pk_name = legacy_model._meta.pk.name

        # Clear all model entries
        # They may have been created in a previous migration attempt
        model.objects.all().delete()

        # setup migration strategy for tables with or without a pk
        if legacy_pk_name == 'id':
            # There is no pk in the legacy table
            def save(new, old):
                new.save()

            old_records = iter_sql_records(
                'select * from ' + legacy_model._meta.db_table, 'legacy')
        else:
            def save(new, old):
                save_with_id(new, getattr(old, legacy_pk_name))

            old_records = legacy_model.objects.all().order_by(legacy_pk_name)

        adjust = MIGRATION_ADJUSTMENTS.get(model)

        # convert old records to new ones
        for old in old_records:
            new = model()
            self.populate_renamed_fields(new, old)
            if adjust:
                adjust(new, old)
            save(new, old)
            if getattr(old, 'ind_excluido', False):
                self.to_delete.append(new)


def migrate(obj=appconfs):
    dm = DataMigrator()
    dm.migrate(obj)


# MIGRATION_ADJUSTMENTS #####################################################

def adjust_participacao(new_participacao, old):
    composicao = Composicao()
    composicao.comissao, composicao.periodo = [
        get_fk_related(Composicao._meta.get_field(name), value)
        for name, value in (('comissao', old.cod_comissao),
                            ('periodo', old.cod_periodo_comp))]
    # check if there is already an "equal" one in the db
    already_created = Composicao.objects.filter(
        comissao=composicao.comissao, periodo=composicao.periodo)
    if already_created:
        assert len(already_created) == 1  # we must never have made 2 copies
        [composicao] = already_created
    else:
        composicao.save()
    new_participacao.composicao = composicao


def adjust_parlamentar(new_parlamentar, old):
    value = new_parlamentar.unidade_deliberativa
    # Field is defined as not null in legacy db,
    # but data includes null values
    #  => transform None to False
    if value is None:
        warn('null converted to False')
        new_parlamentar.unidade_deliberativa = False


def adjust_sessaoplenaria(new, old):
    assert not old.tip_expediente


MIGRATION_ADJUSTMENTS = {
    Participacao: adjust_participacao,
    Parlamentar: adjust_parlamentar,
    SessaoPlenaria: adjust_sessaoplenaria,
}

# CHECKS ####################################################################


def get_ind_excluido(obj):
    legacy_model = legacy_app.get_model(type(obj).__name__)
    return getattr(legacy_model.objects.get(
        **{legacy_model._meta.pk.name: obj.id}), 'ind_excluido', False)


def check_app_no_ind_excluido(app):
    for model in app.models.values():
        assert not any(get_ind_excluido(obj) for obj in model.objects.all())
    print('OK!')
