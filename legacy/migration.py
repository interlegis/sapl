import re

import pkg_resources
import yaml
from django.apps import apps
from django.apps.config import AppConfig
from django.core.exceptions import ObjectDoesNotExist
from django.db import connections, models
from django.db.models import CharField, TextField
from django.db.models.base import ModelBase
from model_mommy import mommy
from model_mommy.mommy import foreign_key_required, make

from base.models import ProblemaMigracao
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

unique_constraints = []

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
    print('CUIDADO! ' + msg)


def get_fk_related(field, value, label=None):
    if value is None and field.null is False:
        value = 0
    if value is not None:
        try:
            value = field.related_model.objects.get(id=value)
        except ObjectDoesNotExist:
            msg = 'FK [%s] não encontrada para valor %s ' \
                '(em %s %s)' % (
                    field.name, value,
                    field.model.__name__, label or '---')
            if value == 0:
                if not field.null:
                    fields_dict = get_fields_dict(field.related_model)
                    value = mommy.make(field.related_model,
                                       **fields_dict)
                    descricao = 'stub criado para campos não nuláveis!'
                    save_relation(value, msg, descricao, eh_stub=True)
                    warn(msg + ' => ' + descricao)
                else:
                    value = None
            else:
                value = make_stub(field.related_model, value)
                descricao = 'stub criado para entrada orfã!'
                warn(msg + ' => ' + descricao)
                save_relation(value, msg, descricao, eh_stub=True)
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
    class Record:
        pass
    cursor = exec_sql(sql, db)
    fieldnames = [name[0] for name in cursor.description]
    for row in cursor.fetchall():
        record = Record()
        record.__dict__.update(zip(fieldnames, row))
        yield record


def delete_constraints(model):
    # pega nome da unique constraint dado o nome da tabela
    table = model._meta.db_table
    cursor = exec_sql("SELECT conname FROM pg_constraint WHERE conrelid = "
                      "(SELECT oid FROM pg_class WHERE relname LIKE "
                      "'%s') and contype = 'u';" % (table))
    result = cursor.fetchone()
    # se existir um resultado, unique constraint será deletado
    if result:
        warn('Excluindo unique constraint de nome %s' % result)
        args = model._meta.unique_together[0]
        args_list = list(args)
        unique_constraints.append([table, result[0], args_list, model])
        exec_sql("ALTER TABLE %s DROP CONSTRAINT %s;" %
                 (table, result[0]))


def recreate_constraints():
    if unique_constraints:
        for constraint in unique_constraints:
            table, name, args, model = constraint
            for i in range(len(args)):
                if isinstance(model._meta.get_field(args[i]),
                              models.ForeignKey):
                    args[i] = args[i] + '_id'
            args_string = ''
            args_string += "(" + ', '.join(map(str, args)) + ")"
            exec_sql("ALTER TABLE %s ADD CONSTRAINT %s UNIQUE %s;" %
                     (table, name, args_string))
    unique_constraints.clear()


def stub_desnecessario(obj):
    lista_fields = [
        f for f in obj._meta.get_fields()
        if (f.one_to_many or f.one_to_one) and f.auto_created
    ]
    desnecessario = not any(
        rr.related_model.objects.filter(**{rr.field.name: obj}).exists()
        for rr in lista_fields)
    return desnecessario


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


def save_relation(obj, problema='', descricao='', eh_stub=False):
    link = ProblemaMigracao(content_object=obj, problema=problema,
                            descricao=descricao, eh_stub=eh_stub)
    link.save()


def make_stub(model, id):
    fields_dict = get_fields_dict(model)
    new = mommy.prepare(model, **fields_dict)
    save_with_id(new, id)

    return new


def get_fields_dict(model):
    all_fields = model._meta.get_fields()
    fields_dict = {}
    fields_dict = {f.name: '????????????'[:f.max_length]
                   for f in all_fields
                   if isinstance(f, (CharField, TextField)) and
                   not f.choices and not f.blank}
    return fields_dict


class DataMigrator:
    def __init__(self):
        self.field_renames, self.model_renames = get_renames()
        self.data_mudada = {}

    def populate_renamed_fields(self, new, old):
        renames = self.field_renames[type(new)]

        for field in new._meta.fields:
            old_field_name = renames.get(field.name)
            field_type = field.get_internal_type()
            msg = ("O valor do campo %s (%s) da model %s era inválido" %
                   (field.name, field_type, field.model.__name__))
            if old_field_name:
                old_value = getattr(old, old_field_name)
                if isinstance(field, models.ForeignKey):
                    old_type = type(old)  # not necessarily a model
                    if hasattr(old_type, '_meta') and \
                            old_type._meta.pk.name != 'id':
                        label = old.pk
                    else:
                        label = '-- SEM PK --'
                    value = get_fk_related(field, old_value, label)
                else:
                    value = getattr(old, old_field_name)
                if (field_type == 'DateField' and
                        field.null is False and value is None):
                    names = [old_fields.name for old_fields
                             in old._meta.get_fields()]
                    combined_names = "(" + ")|(".join(names) + ")"
                    matches = re.search('(ano_\w+)', combined_names)
                    if not matches:
                        descricao = 'A data 0001-01-01 foi colocada no lugar'
                        warn(msg +
                             ' => ' + descricao)
                        value = '0001-01-01'
                        self.data_mudada['obj'] = new
                        self.data_mudada['descricao'] = descricao
                        self.data_mudada['problema'] = msg
                    else:
                        value = '%d-01-01' % getattr(old, matches.group(0))
                        descricao = ('A data %s para foi colocada no lugar'
                                     % value)
                        self.data_mudada['obj'] = new
                        self.data_mudada['descricao'] = descricao
                        self.data_mudada['problema'] = msg
                        warn(msg +
                             '=> ' + descricao)
                if field_type == 'CharField' or field_type == 'TextField':
                    if value is None:
                        value = ''
                setattr(new, field.name, value)

    def migrate(self, obj=appconfs):
        # warning: model/app migration order is of utmost importance

        self.to_delete = []
        ProblemaMigracao.objects.all().delete()
        info('Começando migração: %s...' % obj)
        self._do_migrate(obj)
        # exclude logically deleted in legacy base
        info('Deletando models com ind_excluido...')
        for obj in self.to_delete:
            obj.delete()
        info('Deletando stubs desnecessários...')
        while self.delete_stubs():
            pass
        info('Recriando unique constraints...')
        recreate_constraints()

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
        print('Migrando %s...' % model.__name__)

        legacy_model_name = self.model_renames.get(model, model.__name__)
        legacy_model = legacy_app.get_model(legacy_model_name)
        legacy_pk_name = legacy_model._meta.pk.name

        # Clear all model entries
        # They may have been created in a previous migration attempt
        model.objects.all().delete()
        delete_constraints(model)

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
            if self.data_mudada:
                save_relation(**self.data_mudada)
                self.data_mudada.clear()
            if getattr(old, 'ind_excluido', False):
                self.to_delete.append(new)

    def delete_stubs(self):
        excluidos = 0
        for obj in ProblemaMigracao.objects.all():
            if obj.content_object and obj.eh_stub:
                original = obj.content_type.get_all_objects_for_this_type(
                    id=obj.object_id)
                if stub_desnecessario(original[0]):
                    qtd_exclusoes, *_ = original.delete()
                    assert qtd_exclusoes == 1
                    qtd_exclusoes, *_ = obj.delete()
                    assert qtd_exclusoes == 1
                    excluidos = excluidos + 1
            elif not obj.content_object and not obj.eh_stub:
                qtd_exclusoes, *_ = obj.delete()
                assert qtd_exclusoes == 1
                excluidos = excluidos + 1
        return excluidos


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
    if old.ind_unid_deliberativa:
        value = new_parlamentar.unidade_deliberativa
        # Field is defined as not null in legacy db,
        # but data includes null values
        #  => transform None to False
        if value is None:
            warn('nulo convertido para falso')
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

# MOMMY MAKE WITH LOG  ######################################################


def make_with_log(model, _quantity=None, make_m2m=False, **attrs):
    fields_dict = get_fields_dict(model)
    stub = make(model, _quantity, make_m2m, **fields_dict)
    problema = 'Um stub foi necessário durante a criação de um outro stub'
    descricao = 'Essa entrada é necessária para um dos stubs criados'
    ' anteriormente'
    warn(problema)
    save_relation(stub, problema, descricao, eh_stub=True)
    return stub

make_with_log.required = foreign_key_required
