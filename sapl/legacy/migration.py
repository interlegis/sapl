import re
from datetime import date
from subprocess import PIPE, call

import pkg_resources
import reversion
import yaml
from django.apps import apps
from django.apps.config import AppConfig
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError, ProgrammingError, connections, models
from django.db.models import CharField, Max, ProtectedError, TextField
from django.db.models.base import ModelBase
from model_mommy import mommy
from model_mommy.mommy import foreign_key_required, make

from sapl.base.models import Autor, ProblemaMigracao
from sapl.comissoes.models import Comissao, Composicao, Participacao
from sapl.legacy.models import Protocolo as ProtocoloLegado
from sapl.materia.models import (Proposicao, StatusTramitacao, TipoDocumento,
                                 TipoMateriaLegislativa, TipoProposicao,
                                 Tramitacao)
from sapl.norma.models import (AssuntoNorma, NormaJuridica,
                               TipoVinculoNormaJuridica)
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import Protocolo, StatusTramitacaoAdministrativo
from sapl.sessao.models import ExpedienteMateria, OrdemDia, SessaoPlenaria
from sapl.settings import PROJECT_DIR
from sapl.utils import normalize

# BASE ######################################################################
#  apps to be migrated, in app dependency order (very important)
appconfs = [apps.get_app_config(n) for n in [
    'parlamentares',
    'comissoes',
    'base',
    'materia',
    'norma',
    'sessao',
    'lexml',
    'protocoloadm', ]]

unique_constraints = []
one_to_one_constraints = []
primeira_vez = []

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
                    # Cria stub ao final da tabela para evitar erros
                    pk = 1
                    if hasattr(field.related_model.objects.last(), 'pk'):
                        pk = field.related_model.objects.last().pk
                    with reversion.create_revision():
                        reversion.set_comment('Stub criado pela migração')
                        value = mommy.make(
                            field.related_model, **fields_dict,
                            pk=(pk + 1 or 1))
                        descricao = 'stub criado para campos não nuláveis!'
                        save_relation(value, [field.name], msg, descricao,
                                      eh_stub=True)
                        warn(msg + ' => ' + descricao)
                else:
                    value = None
            else:
                if field.model._meta.label == 'sessao.RegistroVotacao' and \
                        field.name == 'ordem':
                    return value
                # Caso TipoProposicao não exista, um objeto será criado então
                # com content_type=13 (ProblemaMigracao)
                if field.related_model.__name__ == 'TipoProposicao':
                    tipo = TipoProposicao.objects.filter(descricao='Erro')
                    if not tipo:
                        with reversion.create_revision():
                            reversion.set_comment(
                                'TipoProposicao "Erro" criado')
                            ct = ContentType.objects.get(pk=13)
                            value = TipoProposicao.objects.create(
                                id=value, descricao='Erro', content_type=ct)
                    else:
                        value = tipo[0]
                else:
                    with reversion.create_revision():
                        reversion.set_comment('Stub criado pela migração')
                        value = make_stub(field.related_model, value)
                        descricao = 'stub criado para entrada orfã!'
                        warn(msg + ' => ' + descricao)
                        save_relation(value, [field.name], msg, descricao,
                                      eh_stub=True)
        else:
            assert value
    return value


def get_field(model, fieldname):
    return model._meta.get_field(fieldname)


def exec_sql_file(path, db='default'):
    cursor = connections[db].cursor()
    for line in open(path):
        try:
            cursor.execute(line)
        except (OperationalError, ProgrammingError) as e:
            print("Args: '%s'" % (str(e.args)))


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
    result = ()
    result = cursor.fetchall()
    # se existir um resultado, unique constraint será deletado
    for r in result:
        if r[0].endswith('key'):
            words_list = r[0].split('_')
            one_to_one_constraints.append([table, r[0], words_list, model])
        else:
            args = None
            args_list = []
            if model._meta.unique_together:
                args = model._meta.unique_together[0]
                args_list = list(args)
            unique_constraints.append([table, r[0], args_list, model])
        warn('Excluindo unique constraint de nome %s' % r[0])
        exec_sql("ALTER TABLE %s DROP CONSTRAINT %s;" %
                 (table, r[0]))


def recreate_constraints():
    if one_to_one_constraints:
        for constraint in one_to_one_constraints:
            table, name, args, model = constraint
            args_string = ''
            args_string = "(" + "_".join(map(str, args[2:-1])) + ")"
            exec_sql("ALTER TABLE %s ADD CONSTRAINT %s UNIQUE %s;" %
                     (table, name, args_string))
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
    one_to_one_constraints.clear()
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


def get_last_value(model):
    last_value = model.objects.all().aggregate(Max('pk'))
    return last_value['pk__max'] if last_value['pk__max'] else 0


def alter_sequence(model, id):
    sequence_name = '%s_id_seq' % model._meta.db_table
    exec_sql('ALTER SEQUENCE %s RESTART WITH %s;' % (sequence_name, id))


def save_with_id(new, id):
    last_value = get_last_value(type(new))
    alter_sequence(type(new), id)
    new.save()
    alter_sequence(type(new), last_value + 1)
    assert new.id == id, 'New id is different from provided!'


def save_relation(obj, nome_campo='', problema='', descricao='',
                  eh_stub=False):
    link = ProblemaMigracao(
        content_object=obj, nome_campo=nome_campo, problema=problema,
        descricao=descricao, eh_stub=eh_stub,
    )
    link.save()


def make_stub(model, id):
    fields_dict = get_fields_dict(model)
    new = mommy.prepare(model, **fields_dict, pk=id)
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


def fill_vinculo_norma_juridica():
    lista = [('A', 'Altera a norma'),
             ('R', 'Revoga integralmente a norma'),
             ('P', 'Revoga parcialmente a norma'),
             ('T', 'Revoga integralmente por consolidação'),
             ('C', 'Norma Correlata'),
             ('S', 'Ressalva a Norma'),
             ('E', 'Reedita a Norma'),
             ('I', 'Reedita a Norma com Alteração'),
             ('G', 'Regulamenta a Norma'),
             ('K', 'Suspende parcialmente a norma'),
             ('L', 'Suspende integralmente a norma'),
             ('N', 'Julgada integralmente inconstitucional'),
             ('O', 'Julgada parcialmente inconstitucional')]
    lista_objs = [TipoVinculoNormaJuridica(sigla=item[0], descricao=item[1])
                  for item in lista]
    TipoVinculoNormaJuridica.objects.bulk_create(lista_objs)


class DataMigrator:

    def __init__(self):
        self.field_renames, self.model_renames = get_renames()
        self.data_mudada = {}
        self.choice_valida = {}

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
                if field_type == 'DateField' and \
                        not field.null and value is None:
                    descricao = 'A data 1111-11-11 foi colocada no lugar'
                    problema = 'O valor da data era nulo ou inválido'
                    warn(msg +
                         ' => ' + descricao)
                    value = date(1111, 11, 11)
                    self.data_mudada['obj'] = new
                    self.data_mudada['descricao'] = descricao
                    self.data_mudada['problema'] = problema
                    self.data_mudada.setdefault('nome_campo', []).\
                        append(field.name)
                if field_type == 'CharField' or field_type == 'TextField':
                    if value is None or value == 'None':
                        value = ''
                if field.model._meta.label == 'sessao.RegistroVotacao' and \
                        field.name == 'ordem' and \
                        not isinstance(value, OrdemDia):
                    try:
                        new_value = ExpedienteMateria.objects.get(pk=value)
                        setattr(new, 'expediente', new_value)
                        setattr(new, field.name, None)
                        continue
                    except ObjectDoesNotExist:
                        msg = 'FK [%s] não encontrada para valor %s ' \
                            '(em %s %s)' % (
                                field.name, value,
                                field.model.__name__, label or '---')
                        with reversion.create_revision():
                            value = make_stub(field.related_model, value)
                            descricao = 'stub criado para entrada orfã!'
                            warn(msg + ' => ' + descricao)
                            save_relation(value, [field.name], msg, descricao,
                                          eh_stub=True)
                            reversion.set_comment('Stub criado pela migração')
                setattr(new, field.name, value)
            elif field.model.__name__ == 'TipoAutor' and \
                    field.name == 'content_type':

                model = normalize(new.descricao.lower()).replace(' ', '')
                content_types = field.related_model.objects.filter(
                    model=model).exclude(app_label='legacy')
                assert len(content_types) <= 1

                value = content_types[0] if content_types else None
                setattr(new, field.name, value)

    def migrate(self, obj=appconfs, interativo=True):
        # warning: model/app migration order is of utmost importance
        exec_sql_file(PROJECT_DIR.child(
            'sapl', 'legacy', 'scripts', 'fix_tables.sql'), 'legacy')
        self.to_delete = []

        # excluindo database antigo.
        if interativo:
            info('Todos os dados do banco serão excluidos. '
                 'Recomendamos que faça backup do banco sapl '
                 'antes de continuar.')
            info('Deseja continuar? [s/n]')
            resposta = input()
            if resposta.lower() in ['s', 'sim', 'y', 'yes']:
                pass
            else:
                info('Migração cancelada.')
                return 0
        info('Excluindo entradas antigas do banco.')
        call([PROJECT_DIR.child('manage.py'), 'flush',
              '--settings=sapl.settings', '--database=default', '--no-input'],
             stdout=PIPE)

        info('Começando migração: %s...' % obj)
        self._do_migrate(obj)
        # exclude logically deleted in legacy base
        info('Deletando models com ind_excluido...')
        while self.to_delete:
            for obj in self.to_delete:
                try:
                    obj.delete()
                    self.to_delete.remove(obj)
                except ProtectedError:
                    msg = 'A entrada de PK %s da model %s não pode ser ' \
                        'excluida' % (obj.pk, obj._meta.model_name)
                    descricao = 'Um ou mais objetos protegidos '
                    warn(msg + ' => ' + descricao)
                    save_relation(obj=obj, problema=msg,
                                  descricao=descricao, eh_stub=False)

        info('Deletando stubs desnecessários...')
        while self.delete_stubs():
            pass
        info('Recriando unique constraints...')
        # recreate_constraints()

    def _do_migrate(self, obj):
        if isinstance(obj, AppConfig):
            models_to_migrate = (model for model in obj.models.values()
                                 if model in self.field_renames)
            self._do_migrate(models_to_migrate)
        elif isinstance(obj, ModelBase):
            # A migração vai pular TipoProposicao e só vai migrar essa model
            # antes de migrar Proposicao. Isso deve acontecer por causa da
            # GenericRelation existente em TipoProposicao.
            if not obj.__name__ == 'TipoProposicao':
                if obj.__name__ == 'Proposicao':
                    self.migrate_model(TipoProposicao)
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
        try:
            model.objects.all().delete()
        except ProtectedError:
            Proposicao.objects.all().delete()
            model.objects.all().delete()
        delete_constraints(model)

        # setup migration strategy for tables with or without a pk
        if legacy_pk_name == 'id':
            # There is no pk in the legacy table
            def save(new, old):
                with reversion.create_revision():
                    new.save()
                    reversion.set_comment('Objeto criado pela migração')
            old_records = iter_sql_records(
                'select * from ' + legacy_model._meta.db_table, 'legacy')
        else:
            def save(new, old):
                with reversion.create_revision():
                    save_with_id(new, getattr(old, legacy_pk_name))
                    reversion.set_comment('Objeto criado pela migração')

            old_records = legacy_model.objects.all().order_by(legacy_pk_name)

        ajuste_antes_salvar = AJUSTE_ANTES_SALVAR.get(model)
        ajuste_depois_salvar = AJUSTE_DEPOIS_SALVAR.get(model)

        # convert old records to new ones
        for old in old_records:
            new = model()
            self.populate_renamed_fields(new, old)
            if ajuste_antes_salvar:
                ajuste_antes_salvar(new, old)
            save(new, old)
            if ajuste_depois_salvar:
                ajuste_depois_salvar(new, old)
            if self.data_mudada:
                with reversion.create_revision():
                    save_relation(**self.data_mudada)
                    self.data_mudada.clear()
                    reversion.set_comment('Ajuste de data pela migração')
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


def migrate(obj=appconfs, interativo=True):
    dm = DataMigrator()
    dm.migrate(obj, interativo)


# MIGRATION_ADJUSTMENTS #####################################################

def adjust_ordemdia(new, old):
    # Prestar atenção
    if not old.tip_votacao:
        new.tipo_votacao = 1


def adjust_parlamentar(new, old):
    if old.ind_unid_deliberativa:
        value = new.unidade_deliberativa
        # Field is defined as not null in legacy db,
        # but data includes null values
        #  => transform None to False
        if value is None:
            warn('nulo convertido para falso')
            new.unidade_deliberativa = False


def adjust_participacao(new, old):
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
        with reversion.create_revision():
            composicao.save()
            reversion.set_comment('Objeto criado pela migração')
    new.composicao = composicao


def adjust_protocolo(new, old):
    if new.numero is None and not primeira_vez:
        p = ProtocoloLegado.objects.filter(
            ano_protocolo=new.ano).aggregate(Max('num_protocolo'))
        new.numero = p['num_protocolo__max'] + 1
        primeira_vez.append(True)
    if new.numero is None and primeira_vez:
        p = Protocolo.objects.filter(
            ano=new.ano).aggregate(Max('numero'))
        new.numero = p['numero__max'] + 1


def adjust_sessaoplenaria(new, old):
    assert not old.tip_expediente


def adjust_tipoproposicao(new, old):
    if old.ind_mat_ou_doc == 'M':
        new.tipo_conteudo_related = TipoMateriaLegislativa.objects.get(
            pk=old.tip_mat_ou_doc)
    elif old.ind_mat_ou_doc == 'D':
        new.tipo_conteudo_related = TipoDocumento.objects.get(
            pk=old.tip_mat_ou_doc)


def adjust_statustramitacao(new, old):
    if old.ind_fim_tramitacao:
        new.indicador = 'F'
    elif old.ind_retorno_tramitacao:
        new.indicador = 'R'
    else:
        new.indicador = ''


def adjust_statustramitacaoadm(new, old):
    adjust_statustramitacao(new, old)


def adjust_tramitacao(new, old):
    if old.sgl_turno == 'Ú':
        new.turno = 'U'


def adjust_normajuridica_antes_salvar(new, old):
    # Ajusta choice de esfera_federacao
    # O 'S' vem de 'Selecionar'. Na versão antiga do SAPL, quando uma opção do
    # combobox era selecionada, o sistema pegava a primeira letra da seleção,
    # sendo F para Federal, E para Estadual, M para Municipal e o S para
    # Selecionar, que era a primeira opção quando nada era selecionado.
    if old.tip_esfera_federacao == 'S':
        new.esfera_federacao = ''


def adjust_normajuridica_depois_salvar(new, old):
    # Ajusta relação M2M
    lista_pks_assunto = old.cod_assunto.split(',')
    for pk_assunto in lista_pks_assunto:
        new.assuntos.add(AssuntoNorma.objects.get(pk=pk_assunto))


def adjust_protocolo_depois_salvar(new, old):
    if old.num_protocolo is None:
        with reversion.create_revision():
            problema = 'Número do protocolo de PK %s é nulo' % new.pk
            descricao = 'Número do protocolo alterado para %s!' % new.numero
            warn(problema + ' => ' + descricao)
            save_relation(obj=new, problema=problema,
                          descricao=descricao, eh_stub=False)
            reversion.set_comment('Numero de protocolo teve que ser alterado')


def adjust_autor(new, old):
    if old.cod_parlamentar:
        new.autor_related = Parlamentar.objects.get(pk=old.cod_parlamentar)
        new.nome = new.autor_related.nome_parlamentar
    elif old.cod_comissao:
        new.autor_related = Comissao.objects.get(pk=old.cod_comissao)

    if old.col_username:
        if not get_user_model().objects.filter(
                username=old.col_username).exists():
            user = get_user_model()(
                username=old.col_username, password=12345)
            with reversion.create_revision():
                user.save()
                reversion.set_comment('Objeto criado pela migração')
            new.user = user
        else:
            new.user = get_user_model().objects.filter(
                username=old.col_username)[0]


def adjust_comissao(new, old):
    if old.dat_extincao:
        if date.today() < new.data_extincao:
            new.ativa = True
        else:
            new.ativa = False
    if not old.dat_extincao:
        new.ativa = True


AJUSTE_ANTES_SALVAR = {
    Autor: adjust_autor,
    Comissao: adjust_comissao,
    NormaJuridica: adjust_normajuridica_antes_salvar,
    OrdemDia: adjust_ordemdia,
    Parlamentar: adjust_parlamentar,
    Participacao: adjust_participacao,
    Protocolo: adjust_protocolo,
    SessaoPlenaria: adjust_sessaoplenaria,
    TipoProposicao: adjust_tipoproposicao,
    StatusTramitacao: adjust_statustramitacao,
    StatusTramitacaoAdministrativo: adjust_statustramitacaoadm,
    Tramitacao: adjust_tramitacao,
}

AJUSTE_DEPOIS_SALVAR = {
    NormaJuridica: adjust_normajuridica_depois_salvar,
    Protocolo: adjust_protocolo_depois_salvar,
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
    last_value = get_last_value(model)
    alter_sequence(model, last_value + 1)
    fields_dict = get_fields_dict(model)
    stub = make(model, _quantity, make_m2m, **fields_dict)
    problema = 'Um stub foi necessário durante a criação de um outro stub'
    descricao = 'Essa entrada é necessária para um dos stubs criados'
    ' anteriormente'
    warn(problema)
    save_relation(obj=stub, problema=problema,
                  descricao=descricao, eh_stub=True)
    return stub

make_with_log.required = foreign_key_required
