import os
import re
from datetime import date
from functools import lru_cache, partial
from itertools import groupby
from subprocess import PIPE, call

import pkg_resources
import reversion
import yaml
from django.apps import apps
from django.apps.config import AppConfig
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import connections, transaction
from django.db.models import Count, Max
from django.db.models.base import ModelBase
from pytz import timezone

from sapl.base.models import AppConfig as AppConf
from sapl.base.models import (Autor, ProblemaMigracao, TipoAutor,
                              cria_models_tipo_autor)
from sapl.comissoes.models import Comissao, Composicao, Participacao
from sapl.legacy.models import TipoNumeracaoProtocolo
from sapl.materia.models import (AcompanhamentoMateria, Proposicao,
                                 StatusTramitacao, TipoDocumento,
                                 TipoMateriaLegislativa, TipoProposicao,
                                 Tramitacao)
from sapl.norma.models import (AssuntoNorma, NormaJuridica, NormaRelacionada,
                               TipoVinculoNormaJuridica)
from sapl.parlamentares.models import (Legislatura, Mandato, Parlamentar,
                                       Partido, TipoAfastamento)
from sapl.protocoloadm.models import (DocumentoAdministrativo, Protocolo,
                                      StatusTramitacaoAdministrativo)
from sapl.sessao.models import ExpedienteMateria, OrdemDia, RegistroVotacao
from sapl.settings import DATABASES, PROJECT_DIR
from sapl.utils import normalize

from .timezonesbrasil import get_timezone

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


class ForeignKeyFaltando(ObjectDoesNotExist):
    'Uma FK aponta para um registro inexistente'
    pass


@lru_cache()
def _get_all_ids_from_model(model):
    # esta função para uso apenas em get_fk_related
    return set(model.objects.values_list('id', flat=True))


def get_fk_related(field, value, label=None):
    if value is None and field.null:
        return None

    # if field.related_model.objects.filter(id=value).exists():
    if value in _get_all_ids_from_model(field.related_model):
        return value
    elif value == 0 and field.null:
        # consideramos zeros como nulos, se não está entre os ids anteriores
        return None
    else:
        msg = 'FK [%s] não encontrada para o valor %s (em %s %s)' % (
            field.name, value, field.model.__name__, label or '---')
        warn(msg)
        raise ForeignKeyFaltando(msg)


def exec_sql(sql, db='default'):
    cursor = connections[db].cursor()
    cursor.execute(sql)
    return cursor


exec_legado = partial(exec_sql, db='legacy')


def _formatar_lista_para_sql(iteravel):
    lista = list(iteravel)
    if lista:
        return '({})'.format(str(lista)[1:-1])  # transforma "[...]" em "(...)"
    else:
        return None


def exec_legado_em_subconjunto(sql, ids):
    """Executa uma query sql no legado no formato '.... in {}'
    interpolando `ids`, se houver ids"""

    lista_sql = _formatar_lista_para_sql(ids)
    if lista_sql:
        return exec_legado(sql.format(lista_sql))
    else:
        return []


def primeira_coluna(cursor):
    return (r[0] for r in cursor)


# UNIFORMIZAÇÃO DO BANCO ANTES DA MIGRAÇÃO ###############################

SQL_NAO_TEM_TABELA = '''
   SELECT count(*)
   FROM information_schema.columns
   WHERE table_schema=database()
     AND TABLE_NAME="{}"
'''


def existe_tabela_no_legado(tabela):
    sql = SQL_NAO_TEM_TABELA.format(tabela)
    return list(primeira_coluna(exec_legado(sql)))[0]


def existe_coluna_no_legado(tabela, coluna):
    sql_nao_tem_coluna = SQL_NAO_TEM_TABELA + ' AND COLUMN_NAME="{}"'
    sql = sql_nao_tem_coluna.format(tabela, coluna)
    return list(primeira_coluna(exec_legado(sql)))[0] > 0


def garante_coluna_no_legado(tabela, spec_coluna):
    coluna = spec_coluna.split()[0]
    if not existe_coluna_no_legado(tabela, coluna):
        exec_legado('ALTER TABLE {} ADD COLUMN {}'.format(tabela, spec_coluna))
    assert existe_coluna_no_legado(tabela, coluna)


def garante_tabela_no_legado(create_table):
    tabela = create_table.strip().splitlines()[0].split()[2]
    if not existe_tabela_no_legado(tabela):
        exec_legado(create_table)
        assert existe_tabela_no_legado(tabela)


TABELAS_REFERENCIANDO_AUTOR = [
    # <nome da tabela>, <tem ind excluido>
    ('autoria', True),
    ('documento_administrativo', True),
    ('proposicao', True),
    ('protocolo', False)]


def reverte_exclusao_de_autores_referenciados_no_legado():
    """Reverte a exclusão de autores que sejam referenciados de alguma forma
    na base legada"""

    def get_autores_referenciados(tabela, tem_ind_excluido):
        sql = '''select distinct cod_autor from {}
                 where cod_autor is not null
              '''.format(tabela)
        if tem_ind_excluido:
            sql += ' and ind_excluido != 1'
        return primeira_coluna(exec_legado(sql))

    # reverte exclusões de autores referenciados por outras tabelas
    autores_referenciados = {
        cod
        for tabela, tem_ind_excluido in TABELAS_REFERENCIANDO_AUTOR
        for cod in get_autores_referenciados(tabela, tem_ind_excluido)}
    exec_legado_em_subconjunto(
        'update autor set ind_excluido = 0 where cod_autor in {}',
        autores_referenciados)


def get_reapontamento_de_autores_repetidos(autores):
    """ Dada uma lista ordenada de pares (cod_zzz, cod_autor) retorna:

    * a lista de grupos de cod_autor'es repetidos
      (quando há mais de um cod_autor para um mesmo cod_zzz)

    * a lista de cod_autor'es a serem apagados (todos além do 1o de cada grupo)
    """
    grupos_de_repetidos = [
        [cod_autor for _, cod_autor in grupo]
        for cod_zzz, grupo in groupby(autores, lambda r: r[0])]
    # mantém apenas os grupos com mais de um autor por cod_zzz
    grupos_de_repetidos = [g for g in grupos_de_repetidos if len(g) > 1]
    # aponta cada autor de cada grupo de repetidos para o 1o do seu grupo
    reapontamento = {autor: grupo[0]
                     for grupo in grupos_de_repetidos
                     for autor in grupo}
    # apagaremos todos menos o primeiro
    apagar = [k for k, v in reapontamento.items() if k != v]
    return reapontamento, apagar


def get_autorias_sem_repeticoes(autoria, reapontamento):
    "Autorias sem repetições de autores e com ind_primeiro_autor ajustado"

    # substitui cada autor repetido pelo 1o de seu grupo
    autoria = sorted((reapontamento[a], m, i) for a, m, i in autoria)
    # agrupa por [autor (1o do grupo de repetidos), materia], com
    # ind_primeiro_autor == 1 se isso acontece em qualquer autor do grupo
    autoria = [(a, m, max(i for a, m, i in grupo))
               for (a, m), grupo in groupby(autoria, lambda x: x[:2])]
    return autoria


def unifica_autores_repetidos_no_legado(campo_agregador):
    "Reúne autores repetidos em um único, antes da migracão"

    # enumeramos a repeticoes segundo o campo relevante
    # (p. ex. cod_parlamentar ou cod_comissao)
    # a ordenação prioriza, as entradas:
    #  - não excluidas,
    #  - em seguida as que têm col_username,
    #  - em seguida as que têm des_cargo
    autores = exec_legado('''
            select {cod_parlamentar}, cod_autor from autor
            where {cod_parlamentar} is not null
            order by {cod_parlamentar},
            ind_excluido, col_username desc, des_cargo desc'''.format(
        cod_parlamentar=campo_agregador))

    reapontamento, apagar = get_reapontamento_de_autores_repetidos(autores)

    # se não houver autores repetidos encerramos por aqui
    if not reapontamento:
        return

    # Reaponta AUTORIA (many-to-many)

    # simplificamos retirando inicialmente as autorias excluidas
    exec_legado('delete from autoria where ind_excluido = 1')

    # selecionamos as autorias envolvidas em repetições de autores
    from_autoria = ' from autoria where cod_autor in {}'
    autoria = exec_legado_em_subconjunto(
        'select cod_autor, cod_materia, ind_primeiro_autor' + from_autoria,
        reapontamento)

    # apagamos todas as autorias envolvidas
    exec_legado_em_subconjunto('delete ' + from_autoria, reapontamento)
    # e depois inserimos apenas as sem repetições c ind_primeiro_autor ajustado
    nova_autoria = get_autorias_sem_repeticoes(autoria, reapontamento)
    exec_legado('''
        insert into autoria
        (cod_autor, cod_materia, ind_primeiro_autor, ind_excluido)
        values {}'''.format(', '.join([str((a, m, i, 0))
                                       for a, m, i in nova_autoria])))

    # Reaponta outras tabelas que referenciam autor
    for tabela, _ in TABELAS_REFERENCIANDO_AUTOR:
        for antigo, novo in reapontamento.items():
            if antigo != novo:
                exec_legado('''
                    update {} set cod_autor = {} where cod_autor = {}
                    '''.format(tabela, novo, antigo))

    # Finalmente excluimos os autores redundantes,
    # cujas referências foram todas substituídas a essa altura
    exec_legado_em_subconjunto('delete from autor where cod_autor in {}',
                               apagar)


def anula_tipos_origem_externa_invalidos():
    """Anula tipos de origem externa inválidos
    para que não impeçam a migração da matéria"""

    tipos_validos = primeira_coluna(exec_legado('''
        select tip_materia
        from tipo_materia_legislativa
        where ind_excluido <> 1;'''))

    exec_legado_em_subconjunto('''
        update materia_legislativa
        set tip_origem_externa = NULL
        where tip_origem_externa not in {};''', tipos_validos)


def uniformiza_banco():
    # desliga todas as checagens do mysql
    exec_legado('SET SESSION sql_mode = "";')

    garante_coluna_no_legado('proposicao',
                             'num_proposicao int(11) NULL')

    garante_coluna_no_legado('tipo_materia_legislativa',
                             'ind_num_automatica BOOLEAN NULL DEFAULT FALSE')

    garante_coluna_no_legado('tipo_materia_legislativa',
                             'quorum_minimo_votacao int(11) NULL')

    # Cria campos cod_presenca_sessao (sendo a nova PK da tabela)
    # e dat_sessao em sessao_plenaria_presenca
    if not existe_coluna_no_legado('sessao_plenaria_presenca',
                                   'cod_presenca_sessao'):
        exec_legado('''
            ALTER TABLE sessao_plenaria_presenca
            DROP PRIMARY KEY,
            ADD cod_presenca_sessao INT auto_increment PRIMARY KEY FIRST;
        ''')
        assert existe_coluna_no_legado('sessao_plenaria_presenca',
                                       'cod_presenca_sessao')

    garante_coluna_no_legado('sessao_plenaria_presenca',
                             'dat_sessao DATE NULL')

    garante_tabela_no_legado('''
        CREATE TABLE lexml_registro_publicador (
            cod_publicador INT auto_increment NOT NULL,
            id_publicador INT, nom_publicador varchar(255),
            adm_email varchar(50),
            sigla varchar(255),
            nom_responsavel varchar(255),
            tipo varchar(50),
            id_responsavel INT, PRIMARY KEY (cod_publicador));
    ''')

    garante_tabela_no_legado('''
        CREATE TABLE lexml_registro_provedor (
            cod_provedor INT auto_increment NOT NULL,
            id_provedor INT, nom_provedor varchar(255),
            sgl_provedor varchar(15),
            adm_email varchar(50),
            nom_responsavel varchar(255),
            tipo varchar(50),
            id_responsavel INT, xml_provedor longtext,
            PRIMARY KEY (cod_provedor));
    ''')

    garante_tabela_no_legado('''
        CREATE TABLE tipo_situacao_militar (
            tip_situacao_militar INT auto_increment NOT NULL,
            des_tipo_situacao varchar(50),
            ind_excluido INT, PRIMARY KEY (tip_situacao_militar));
    ''')

    update_specs = '''
vinculo_norma_juridica| ind_excluido = ''           | trim(ind_excluido) = '0'
unidade_tramitacao    | cod_parlamentar = NULL      | cod_parlamentar = 0
parlamentar           | cod_nivel_instrucao = NULL  | cod_nivel_instrucao = 0
parlamentar           | tip_situacao_militar = NULL | tip_situacao_militar = 0
mandato               | tip_afastamento = NULL      | tip_afastamento = 0
relatoria             | tip_fim_relatoria = NULL    | tip_fim_relatoria = 0
    '''.strip().splitlines()

    for spec in update_specs:
        spec = spec.split('|')
        exec_legado('UPDATE {} SET {} WHERE {}'.format(*spec))

    # retira apontamentos de materia para assunto inexistente
    exec_legado('delete from materia_assunto where cod_assunto = 0')

    # corrige string "None" em autor
    exec_legado('update autor set des_cargo = NULL where des_cargo = "None"')

    unifica_autores_repetidos_no_legado('cod_parlamentar')
    unifica_autores_repetidos_no_legado('cod_comissao')

    # é importante reverter a exclusão de autores somente depois, para que a
    # unificação possa dar prioridade às informações dos autores não excluídos
    reverte_exclusao_de_autores_referenciados_no_legado()

    anula_tipos_origem_externa_invalidos()


def iter_sql_records(sql, db):
    class Record:
        pass
    cursor = exec_sql(sql, db)
    fieldnames = [name[0] for name in cursor.description]
    for row in cursor.fetchall():
        record = Record()
        record.__dict__.update(zip(fieldnames, row))
        yield record


def save_relation(obj, nome_campo='', problema='', descricao='',
                  eh_stub=False, critico=False):
    link = ProblemaMigracao(
        content_object=obj, nome_campo=nome_campo, problema=problema,
        descricao=descricao, eh_stub=eh_stub, critico=critico)
    link.save()


def fill_vinculo_norma_juridica():
    lista = [('A', 'Altera o(a)',
              'Alterado(a) pelo(a)'),
             ('R', 'Revoga integralmente o(a)',
              'Revogado(a) integralmente pelo(a)'),
             ('P', 'Revoga parcialmente o(a)',
              'Revogado(a) parcialmente pelo(a)'),
             ('T', 'Revoga integralmente por consolidação',
              'Revogado(a) integralmente por consolidação'),
             ('C', 'Norma correlata',
              'Norma correlata'),
             ('S', 'Ressalva o(a)',
              'Ressalvada pelo(a)'),
             ('E', 'Reedita o(a)',
              'Reeditada pelo(a)'),
             ('I', 'Reedita com alteração o(a)',
              'Reeditada com alteração pelo(a)'),
             ('G', 'Regulamenta o(a)',
              'Regulamentada pelo(a)'),
             ('K', 'Suspende parcialmente o(a)',
              'Suspenso(a) parcialmente pelo(a)'),
             ('L', 'Suspende integralmente o(a)',
              'Suspenso(a) integralmente pelo(a)'),
             ('N', 'Julga integralmente inconstitucional',
              'Julgada integralmente inconstitucional'),
             ('O', 'Julga parcialmente inconstitucional',
              'Julgada parcialmente inconstitucional')]
    lista_objs = [TipoVinculoNormaJuridica(
        sigla=item[0], descricao_ativa=item[1], descricao_passiva=item[2])
        for item in lista]
    TipoVinculoNormaJuridica.objects.bulk_create(lista_objs)


def fill_dados_basicos():
    # Ajusta sequencia numérica e cria base.AppConfig
    letra = 'A'
    try:
        tipo = TipoNumeracaoProtocolo.objects.latest('dat_inicial_protocolo')
        if 'POR ANO' in tipo.des_numeracao_protocolo:
            letra = 'A'
        elif 'POR LEGISLATURA' in tipo.des_numeracao_protocolo:
            letra = 'L'
        elif 'CONSECUTIVO' in tipo.des_numeracao_protocolo:
            letra = 'U'
    except Exception as e:
        pass
    appconf = AppConf(sequencia_numeracao=letra)
    appconf.save()


# Uma anomalia no sapl 2.5 causa a duplicação de registros de votação.
# Essa duplicação deve ser eliminada para que não haja erro no sapl 3.1
def excluir_registrovotacao_duplicados():
    duplicatas_ids = RegistroVotacao.objects.values(
        'materia', 'ordem', 'expediente').annotate(
            Count('id')).order_by().filter(id__count__gt=1)
    duplicatas_queryset = RegistroVotacao.objects.filter(
        materia__in=[item['materia'] for item in duplicatas_ids])

    for dup in duplicatas_queryset:
        lista_dups = duplicatas_queryset.filter(
            materia=dup.materia, expediente=dup.expediente, ordem=dup.ordem)
        primeiro_registro = lista_dups[0]
        lista_dups = lista_dups.exclude(pk=primeiro_registro.pk)
        for objeto in lista_dups:
            if (objeto.pk > primeiro_registro.pk):
                try:
                    objeto.delete()
                except:
                    assert 0
            else:
                try:
                    primeiro_registro.delete()
                    primeiro_registro = objeto
                except:
                    assert 0


def delete_old(legacy_model, cols_values):
    # ajuste necessário por conta de cósigos html em txt_expediente
    if legacy_model.__name__ == 'ExpedienteSessaoPlenaria':
        cols_values.pop('txt_expediente')

    def eq_clause(col, value):
        if value is None:
            return '{} IS NULL'.format(col)
        else:
            return '{}="{}"'.format(col, value)

    delete_sql = 'delete from {} where {}'.format(
        legacy_model._meta.db_table,
        ' and '.join([eq_clause(col, value)
                      for col, value in cols_values.items()]))
    exec_sql(delete_sql, 'legacy')


def get_last_pk(model):
    last_value = model.objects.all().aggregate(Max('pk'))
    return last_value['pk__max'] or 0


def reinicia_sequence(model, id):
    sequence_name = '%s_id_seq' % model._meta.db_table
    exec_sql('ALTER SEQUENCE %s RESTART WITH %s MINVALUE -1;' % (
        sequence_name, id))


class DataMigrator:

    def __init__(self):
        self.field_renames, self.model_renames = get_renames()
        self.data_mudada = {}
        self.choice_valida = {}

        # configura timezone de migração
        nome_legado = DATABASES['legacy']['NAME']
        match = re.match('sapl_cm_(.*)', nome_legado)
        sigla_casa = match.group(1)
        with open(os.path.expanduser('~/sapl_dumps/tabela_timezones.yaml'), 'r') as arq:
            tabela_timezones = yaml.load(arq)
        municipio, uf, nome_timezone = tabela_timezones[sigla_casa]
        if nome_timezone:
            self.timezone = timezone(nome_timezone)
        else:
            self.timezone = get_timezone(municipio, uf)

    def populate_renamed_fields(self, new, old):
        renames = self.field_renames[type(new)]

        for field in new._meta.fields:
            old_field_name = renames.get(field.name)
            field_type = field.get_internal_type()
            if old_field_name:
                old_value = getattr(old, old_field_name)

                if field_type == 'ForeignKey':
                    # not necessarily a model
                    if hasattr(old, '_meta') and old._meta.pk.name != 'id':
                        label = old.pk
                    else:
                        label = '-- SEM PK --'
                    fk_field_name = '{}_id'.format(field.name)
                    value = get_fk_related(field, old_value, label)
                    setattr(new, fk_field_name, value)
                else:
                    value = getattr(old, old_field_name)
                    # TODO rever esse DateField após as mudança para datas com
                    # timezone
                    if field_type == 'DateField' and \
                            not field.null and value is None:
                        # TODO REVER ISSO
                        descricao = 'A data 1111-11-11 foi colocada no lugar'
                        problema = 'O valor da data era nulo ou inválido'
                        warn("O valor do campo %s (%s) do model %s "
                             "era inválido => %s" % (
                                 field.name, field_type,
                                 field.model.__name__, descricao))
                        value = date(1111, 11, 11)
                        self.data_mudada['obj'] = new
                        self.data_mudada['descricao'] = descricao
                        self.data_mudada['problema'] = problema
                        self.data_mudada.setdefault('nome_campo', []).\
                            append(field.name)
                    if (field_type in ['CharField', 'TextField']
                            and value in [None, 'None']):
                        value = ''

                    # adiciona timezone faltante aos campos com tempo
                    #   os campos TIMESTAMP do mysql são gravados em UTC
                    #   os DATETIME e TIME não têm timezone
                    if (field_type in ['DateTimeField', 'TimeField']
                            and value and not value.tzinfo):
                        value = self.timezone.localize(value)
                    setattr(new, field.name, value)

    def migrate(self, obj=appconfs, interativo=True):
        # warning: model/app migration order is of utmost importance

        uniformiza_banco()

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
              '--database=default', '--no-input'], stdout=PIPE)

        # apaga tipos de autor padrão (criados no flush acima)
        TipoAutor.objects.all().delete()

        fill_vinculo_norma_juridica()
        fill_dados_basicos()
        info('Começando migração: %s...' % obj)
        self._do_migrate(obj)

        info('Excluindo possíveis duplicações em RegistroVotacao...')
        excluir_registrovotacao_duplicados()

        # recria tipos de autor padrão que não foram criados pela migração
        cria_models_tipo_autor()

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

        # setup migration strategy for tables with or without a pk
        if legacy_pk_name == 'id':
            deve_ajustar_sequence_ao_final = False
            # There is no pk in the legacy table

            def save(new, old):
                with reversion.create_revision():
                    new.save()
                    reversion.set_comment('Objeto criado pela migração')

                # apaga registro do legado
                delete_old(legacy_model, old.__dict__)

            old_records = iter_sql_records(
                'select * from ' + legacy_model._meta.db_table, 'legacy')
        else:
            deve_ajustar_sequence_ao_final = True

            def save(new, old):
                with reversion.create_revision():
                    # salva new com id de old
                    new.id = getattr(old, legacy_pk_name)
                    new.save()
                    reversion.set_comment('Objeto criado pela migração')

                # apaga registro do legado
                delete_old(legacy_model, {legacy_pk_name: new.id})

            old_records = legacy_model.objects.all().order_by(legacy_pk_name)

        ajuste_antes_salvar = AJUSTE_ANTES_SALVAR.get(model)
        ajuste_depois_salvar = AJUSTE_DEPOIS_SALVAR.get(model)

        # convert old records to new ones
        with transaction.atomic():
            for old in old_records:
                if getattr(old, 'ind_excluido', False):
                    # não migramos registros marcados como excluídos
                    continue
                new = model()
                try:
                    self.populate_renamed_fields(new, old)
                    if ajuste_antes_salvar:
                        ajuste_antes_salvar(new, old)
                except ForeignKeyFaltando:
                    # tentamos preencher uma FK e o ojeto relacionado
                    # não existe
                    # então este é um objeo órfão: simplesmente ignoramos
                    continue
                else:
                    save(new, old)
                    if ajuste_depois_salvar:
                        ajuste_depois_salvar(new, old)

                    if self.data_mudada:
                        with reversion.create_revision():
                            save_relation(**self.data_mudada)
                            self.data_mudada.clear()
                            reversion.set_comment(
                                'Ajuste de data pela migração')
            # reinicia sequence
            if deve_ajustar_sequence_ao_final:
                last_pk = get_last_pk(model)
                reinicia_sequence(model, last_pk + 1)


def migrate(obj=appconfs, interativo=True):
    dm = DataMigrator()
    dm.migrate(obj, interativo)


# MIGRATION_ADJUSTMENTS #####################################################

def adjust_acompanhamentomateria(new, old):
    new.confirmado = True


def adjust_documentoadministrativo(new, old):
    if old.num_protocolo:
        protocolo = Protocolo.objects.filter(
            numero=old.num_protocolo, ano=new.ano)
        if not protocolo:
            protocolo = Protocolo.objects.filter(
                numero=old.num_protocolo, ano=new.ano + 1)
            print('PROTOCOLO ENCONTRADO APENAS PARA O ANO SEGUINTE!!!!! '
                  'DocumentoAdministrativo: {}, numero_protocolo: {}, '
                  'ano doc adm: {}'.format(
                      old.cod_documento, old.num_protocolo, new.ano))
        if not protocolo:
            raise ForeignKeyFaltando(
                'Protocolo {} faltando '
                '(referenciado no documento administrativo {}'.format(
                    old.num_protocolo, old.cod_documento))
        assert len(protocolo) == 1
        new.protocolo = protocolo[0]


def adjust_mandato(new, old):
    if old.dat_fim_mandato:
        new.data_fim_mandato = old.dat_fim_mandato
    if not new.data_fim_mandato:
        legislatura = Legislatura.objects.latest('data_fim')
        new.data_fim_mandato = legislatura.data_fim
        new.data_expedicao_diploma = legislatura.data_inicio
    if not new.data_inicio_mandato:
        new.data_inicio_mandato = new.legislatura.data_inicio
        new.data_fim_mandato = new.legislatura.data_fim


def adjust_ordemdia_antes_salvar(new, old):
    new.votacao_aberta = False

    if not old.tip_votacao:
        new.tipo_votacao = 1

    if old.num_ordem is None:
        new.numero_ordem = 999999999


def adjust_ordemdia_depois_salvar(new, old):
    if old.num_ordem is None and new.numero_ordem == 999999999:
        with reversion.create_revision():
            problema = 'OrdemDia de PK %s tinha seu valor de numero ordem'\
                ' nulo.' % old.pk
            descricao = 'O valor %s foi colocado no lugar.' % new.numero_ordem
            warn(problema + ' => ' + descricao)
            save_relation(obj=new, problema=problema,
                          descricao=descricao, eh_stub=False)
            reversion.set_comment('OrdemDia sem número da ordem.')


def adjust_parlamentar(new, old):
    if old.ind_unid_deliberativa:
        value = new.unidade_deliberativa
        # Field is defined as not null in legacy db,
        # but data includes null values
        #  => transform None to False
        if value is None:
            warn('nulo convertido para falso')
            new.unidade_deliberativa = False
    # migra município de residência
    if old.cod_localidade_resid:
        municipio_uf = list(exec_legado('''
            select nom_localidade, sgl_uf from localidade
            where cod_localidade = {}'''.format(old.cod_localidade_resid)))
        if municipio_uf:
            new.municipio_residencia, new.uf_residencia = municipio_uf[0]


def adjust_participacao(new, old):
    composicao = Composicao()
    composicao.comissao_id, composicao.periodo_id = [
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


def adjust_proposicao_antes_salvar(new, old):
    if new.data_envio:
        new.ano = new.data_envio.year


def adjust_proposicao_depois_salvar(new, old):
    if not hasattr(old.dat_envio, 'year') or old.dat_envio.year == 1800:
        msg = "O valor do campo data_envio (DateField) da model Proposicao"\
            " era inválido"
        descricao = 'A data 1111-11-11 foi colocada no lugar'
        problema = 'O valor da data era nulo ou inválido'
        warn(msg + ' => ' + descricao)
        new.data_envio = date(1111, 11, 11)
        with reversion.create_revision():
            save_relation(obj=new, problema=problema,
                          descricao=descricao, eh_stub=False)
            reversion.set_comment('Ajuste de data pela migração')


def adjust_normarelacionada(new, old):
    tipo = TipoVinculoNormaJuridica.objects.filter(sigla=old.tip_vinculo)
    assert len(tipo) == 1
    new.tipo_vinculo = tipo[0]


def adjust_protocolo_antes_salvar(new, old):
    if old.num_protocolo is None:
        new.numero = old.cod_protocolo


def adjust_protocolo_depois_salvar(new, old):
    if old.num_protocolo is None:
        with reversion.create_revision():
            problema = 'Número do protocolo de PK %s é nulo' % new.pk
            descricao = 'Número do protocolo alterado para %s!' % new.numero
            warn(problema + ' => ' + descricao)
            save_relation(obj=new, problema=problema,
                          descricao=descricao, eh_stub=False)
            reversion.set_comment('Número de protocolo teve que ser alterado')


def adjust_registrovotacao_antes_salvar(new, old):
    ordem_dia = OrdemDia.objects.filter(
        pk=old.cod_ordem, materia=old.cod_materia)
    expediente_materia = ExpedienteMateria.objects.filter(
        pk=old.cod_ordem, materia=old.cod_materia)

    if ordem_dia and not expediente_materia:
        new.ordem = ordem_dia[0]
    if not ordem_dia and expediente_materia:
        new.expediente = expediente_materia[0]


def adjust_registrovotacao_depois_salvar(new, old):
    if not new.ordem and not new.expediente:
        with reversion.create_revision():
            problema = 'RegistroVotacao de PK %s não possui nenhuma OrdemDia'\
                ' ou ExpedienteMateria.' % old.pk
            descricao = 'RevistroVotacao deve ter no mínimo uma ordem do dia'\
                ' ou expediente vinculado.'
            warn(problema + ' => ' + descricao)
            save_relation(obj=new, problema=problema,
                          descricao=descricao, eh_stub=False)
            reversion.set_comment('RegistroVotacao sem ordem ou expediente')


def adjust_tipoafastamento(new, old):
    if old.ind_afastamento == 1:
        new.indicador = 'A'


def adjust_tipoproposicao(new, old):
    if old.ind_mat_ou_doc == 'M':
        tipo_materia = TipoMateriaLegislativa.objects.filter(
            pk=old.tip_mat_ou_doc)
        if tipo_materia:
            new.tipo_conteudo_related = tipo_materia[0]
        else:
            raise ForeignKeyFaltando
    elif old.ind_mat_ou_doc == 'D':
        tipo_documento = TipoDocumento.objects.filter(pk=old.tip_mat_ou_doc)
        if tipo_documento:
            new.tipo_conteudo_related = tipo_documento[0]
        else:
            raise ForeignKeyFaltando


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


def adjust_tipo_autor(new, old):
    model_apontado = normalize(new.descricao.lower()).replace(' ', '')
    content_types = ContentType.objects.filter(
        model=model_apontado).exclude(app_label='legacy')
    assert len(content_types) <= 1
    new.content_type = content_types[0] if content_types else None


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

    if not old.cod_assunto:  # it can be null or empty
        return

    # lista de pks separadas por vírgulas (ignorando strings vazias)
    lista_pks_assunto = [int(pk) for pk in old.cod_assunto.split(',') if pk]

    for pk_assunto in lista_pks_assunto:
        try:
            new.assuntos.add(AssuntoNorma.objects.get(pk=pk_assunto))
        except ObjectDoesNotExist:
            pass  # ignora assuntos inexistentes


def vincula_autor(new, old, model_relacionado, campo_relacionado, campo_nome):
    pk_rel = getattr(old, campo_relacionado)
    if pk_rel:
        try:
            new.autor_related = model_relacionado.objects.get(pk=pk_rel)
        except ObjectDoesNotExist:
            # ignoramos o autor órfão
            raise ForeignKeyFaltando('{} inexiste para autor'.format(
                model_relacionado._meta.verbose_name))
        else:
            new.nome = getattr(new.autor_related, campo_nome)
            return True


def adjust_autor(new, old):
    for args in [
            # essa ordem é importante
            (Parlamentar, 'cod_parlamentar', 'nome_parlamentar'),
            (Comissao, 'cod_comissao', 'nome'),
            (Partido, 'cod_partido', 'nome')]:
        if vincula_autor(new, old, *args):
            break

    if old.col_username:
        user_model = get_user_model()
        if not user_model.objects.filter(username=old.col_username).exists():
            # cria um novo ususaŕio para o autor
            user = user_model(username=old.col_username)
            # gera uma senha inutilizável, que precisará ser trocada
            user.set_password(None)
            with reversion.create_revision():
                user.save()
                reversion.set_comment(
                    'Usuário criado pela migração para o autor {}'.format(
                        old.cod_autor))
            grupo_autor = Group.objects.get(name="Autor")
            user.groups.add(grupo_autor)


def adjust_comissao(new, old):
    if not old.dat_extincao and not old.dat_fim_comissao:
        new.ativa = True
    elif old.dat_extincao and date.today() < new.data_extincao or \
            old.dat_fim_comissao and date.today() < new.data_fim_comissao:
        new.ativa = True
    else:
        new.ativa = False


AJUSTE_ANTES_SALVAR = {
    Autor: adjust_autor,
    TipoAutor: adjust_tipo_autor,
    AcompanhamentoMateria: adjust_acompanhamentomateria,
    Comissao: adjust_comissao,
    DocumentoAdministrativo: adjust_documentoadministrativo,
    Mandato: adjust_mandato,
    NormaJuridica: adjust_normajuridica_antes_salvar,
    NormaRelacionada: adjust_normarelacionada,
    OrdemDia: adjust_ordemdia_antes_salvar,
    Parlamentar: adjust_parlamentar,
    Participacao: adjust_participacao,
    Proposicao: adjust_proposicao_antes_salvar,
    Protocolo: adjust_protocolo_antes_salvar,
    RegistroVotacao: adjust_registrovotacao_antes_salvar,
    TipoAfastamento: adjust_tipoafastamento,
    TipoProposicao: adjust_tipoproposicao,
    StatusTramitacao: adjust_statustramitacao,
    StatusTramitacaoAdministrativo: adjust_statustramitacaoadm,
    Tramitacao: adjust_tramitacao,
}

AJUSTE_DEPOIS_SALVAR = {
    NormaJuridica: adjust_normajuridica_depois_salvar,
    OrdemDia: adjust_ordemdia_depois_salvar,
    Proposicao: adjust_proposicao_depois_salvar,
    Protocolo: adjust_protocolo_depois_salvar,
    RegistroVotacao: adjust_registrovotacao_depois_salvar,
}

# CHECKS ####################################################################


def get_ind_excluido(new):
    legacy_model = legacy_app.get_model(type(new).__name__)
    old = legacy_model.objects.get(**{legacy_model._meta.pk.name: new.id})
    return getattr(old, 'ind_excluido', False)


def check_app_no_ind_excluido(app):
    for model in app.models.values():
        assert not any(get_ind_excluido(new) for new in model.objects.all())
    print('OK!')
