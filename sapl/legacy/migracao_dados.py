import datetime
import os
import re
import subprocess
import traceback
from collections import OrderedDict, defaultdict, namedtuple
from datetime import date
from functools import lru_cache, partial
from itertools import groupby
from operator import xor
from subprocess import PIPE, call

import git
import pkg_resources
import pyaml
import pytz
import reversion
import yaml
from bs4 import BeautifulSoup
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import connections, transaction
from django.db.models import Max, Q
from pyaml import UnsafePrettyYAMLDumper
from unipath import Path

from sapl.base.models import AppConfig as AppConf
from sapl.base.models import Autor, TipoAutor, cria_models_tipo_autor
from sapl.comissoes.models import Comissao, Composicao, Participacao
from sapl.legacy import scripts
from sapl.legacy.models import NormaJuridica as OldNormaJuridica
from sapl.legacy.models import TipoNumeracaoProtocolo
from sapl.legacy_migration_settings import (DATABASES, DIR_DADOS_MIGRACAO,
                                            DIR_REPO, NOME_BANCO_LEGADO,
                                            PROJECT_DIR)
from sapl.materia.models import (AcompanhamentoMateria, MateriaLegislativa,
                                 Proposicao, StatusTramitacao, TipoDocumento,
                                 TipoMateriaLegislativa, TipoProposicao,
                                 Tramitacao)
from sapl.norma.models import (AssuntoNorma, NormaJuridica, NormaRelacionada,
                               TipoVinculoNormaJuridica)
from sapl.parlamentares.models import (Legislatura, Mandato, Parlamentar,
                                       Partido, TipoAfastamento)
from sapl.protocoloadm.models import (DocumentoAdministrativo, Protocolo,
                                      StatusTramitacaoAdministrativo)
from sapl.sessao.models import (ExpedienteMateria, ExpedienteSessao, OrdemDia,
                                RegistroVotacao, TipoResultadoVotacao)
from sapl.utils import normalize

from .scripts.normaliza_dump_mysql import normaliza_dump_mysql
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

# apps quase não têm interseção
name_sets = [(ac.label, set(m.__name__ for m in ac.get_models()))
             for ac in appconfs]
for a1, s1 in name_sets:
    for a2, s2 in name_sets:
        if a1 is not a2:
            # existe uma interseção de nomes entre comissoes e materia
            if {a1, a2} == {'comissoes', 'materia'}:
                assert s1.intersection(s2) == {'DocumentoAcessorio'}
            else:
                assert not s1.intersection(s2)


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


field_renames, model_renames = get_renames()
legacy_app = apps.get_app_config('legacy')
models_novos_para_antigos = {
    model: legacy_app.get_model(model_renames.get(model, model.__name__))
    for model in field_renames}
models_novos_para_antigos[Composicao] = models_novos_para_antigos[Participacao]

content_types = {model: ContentType.objects.get(
    app_label=model._meta.app_label, model=model._meta.model_name)
    for model in field_renames}

campos_novos_para_antigos = {
    model._meta.get_field(nome_novo): nome_antigo
    for model, renames in field_renames.items()
    for nome_novo, nome_antigo in renames.items()}

# campos de Composicao (de Comissao)
for nome_novo, nome_antigo in (('comissao', 'cod_comissao'),
                               ('periodo', 'cod_periodo_comp')):
    campos_novos_para_antigos[
        Composicao._meta.get_field(nome_novo)] = nome_antigo


# campos virtuais de Proposicao para funcionar com get_fk_related
class CampoVirtual(namedtuple('CampoVirtual', 'model related_model')):
    null = True


CAMPOS_VIRTUAIS_PROPOSICAO = {
    TipoMateriaLegislativa: CampoVirtual(Proposicao, MateriaLegislativa),
    TipoDocumento: CampoVirtual(Proposicao, DocumentoAdministrativo)
}
for campo_virtual in CAMPOS_VIRTUAIS_PROPOSICAO.values():
    campos_novos_para_antigos[campo_virtual] = 'cod_mat_ou_doc'


CAMPOS_VIRTUAIS_TIPO_PROPOSICAO = {
    'M': CampoVirtual(TipoProposicao, TipoMateriaLegislativa),
    'D': CampoVirtual(TipoProposicao, TipoDocumento)
}
for campo_virtual in CAMPOS_VIRTUAIS_TIPO_PROPOSICAO.values():
    campos_novos_para_antigos[campo_virtual] = 'tip_mat_ou_doc'


# campos virtuais de Autor para funcionar com get_fk_related
CAMPOS_VIRTUAIS_AUTOR = {related: CampoVirtual(Autor, related)
                         for related in (Parlamentar, Comissao, Partido)}
for related, campo_antigo in [(Parlamentar, 'cod_parlamentar'),
                              (Comissao, 'cod_comissao'),
                              (Partido, 'cod_partido')]:
    campo_virtual = CAMPOS_VIRTUAIS_AUTOR[related]
    campos_novos_para_antigos[campo_virtual] = campo_antigo


# MIGRATION #################################################################


def info(msg):
    print('INFO: ' + msg)


ocorrencias = defaultdict(list)


def warn(tipo, msg, dados):
    ocorrencias[tipo].append(dados)
    print('CUIDADO! ' + msg.format(**dados))


@lru_cache()
def get_pk_legado(tabela):
    if tabela == 'despacho_inicial':
        # adaptação para deleção correta no mysql ao final de migrar_model
        # acompanha o agrupamento de despacho_inicial feito em iter_sql_records
        return 'cod_materia', 'cod_comissao'
    res = exec_legado(
        'show index from {} WHERE Key_name = "PRIMARY"'.format(tabela))
    return [r[4] for r in res]


@lru_cache()
def get_estrutura_legado(model):
    model_legado = models_novos_para_antigos[model]
    tabela_legado = model_legado._meta.db_table
    campos_pk_legado = get_pk_legado(tabela_legado)
    return model_legado, tabela_legado, campos_pk_legado


class ForeignKeyFaltando(ObjectDoesNotExist):
    'Uma FK aponta para um registro inexistente'

    def __init__(self, field, valor, old):
        self.field = field
        self.valor = valor
        self.old = old

    msg = 'FK não encontrada para [{campo} = {valor}] (em {tabela} / pk = {pk})'  # noqa

    @property
    def dados(self):
        campo = campos_novos_para_antigos[self.field]
        _, tabela, campos_pk = get_estrutura_legado(self.field.model)
        pk = {c: getattr(self.old, c) for c in campos_pk}
        sql = 'select * from {} where {};'.format(
            tabela,
            ' and '.join(['{} = {}'.format(k, v) for k, v in pk.items()]))
        return OrderedDict((('campo', campo),
                            ('valor', self.valor),
                            ('tabela', tabela),
                            ('pk', pk),
                            ('sql', sql)))


@lru_cache()
def _get_all_ids_from_model(model):
    # esta função para uso apenas em get_fk_related
    return set(model.objects.values_list('id', flat=True))


def get_fk_related(field, old):
    valor = getattr(old, campos_novos_para_antigos[field])
    if valor is None and field.null:
        return None
    if valor in _get_all_ids_from_model(field.related_model):
        return valor
    elif valor == 0 and field.null:
        # consideramos zeros como nulos, se não está entre os ids anteriores
        return None
    else:
        raise ForeignKeyFaltando(field=field, valor=valor, old=old)


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

    # propaga exclusões para autores não referenciados
    for tabela, fk in [('parlamentar', 'cod_parlamentar'),
                       ('comissao', 'cod_comissao')]:
        sql = '''
            update autor set ind_excluido = 1
            where {cod_parlamentar} is not null
            and {cod_parlamentar} not in (
                select {cod_parlamentar} from {parlamentar}
                where ind_excluido <> 1)
            '''.format(parlamentar=tabela, cod_parlamentar=fk)
        if autores_referenciados:
            sql += ' and cod_autor not in {}'.format(
                tuple(autores_referenciados))
        exec_legado(sql)


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
    if nova_autoria:
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


def get_ids_registros_votacao_para(tabela):
    sql = '''
        select r.cod_votacao from {} o
            inner join registro_votacao r on
            o.cod_ordem = r.cod_ordem and o.cod_materia = r.cod_materia
        where o.ind_excluido != 1 and r.ind_excluido != 1
        order by o.cod_sessao_plen, num_ordem
        '''.format(tabela)
    return set(primeira_coluna(exec_legado(sql)))


def checa_registros_votacao_ambiguos_e_remove_nao_usados():
    """Interrompe a migração caso restem registros de votação
    que apontam para uma ordem_dia e um expediente_materia ao mesmo tempo.

    Remove do legado registros de votação que não têm
    nem ordem_dia nem expediente_materia associados."""

    ordem, expediente = [
        get_ids_registros_votacao_para(tabela)
        for tabela in ('ordem_dia', 'expediente_materia')]

    # interrompe migração se houver registros ambíguos
    ambiguos = ordem.intersection(expediente)
    assert not ambiguos, '''Existe(m) RegistroVotacao ambíguo(s): {}
    Corrija os dados originais antes de migrar!'''.format(
        ambiguos)

    # exclui registros não usados (zumbis)
    todos = set(primeira_coluna(exec_legado(
        'select cod_votacao from registro_votacao')))
    nao_usados = todos - ordem.union(expediente)
    exec_legado_em_subconjunto('''
        update registro_votacao set ind_excluido = 1
        where cod_votacao in {}''', nao_usados)


PROPAGACOES_DE_EXCLUSAO = [
    # sessao_legislativa
    ('sessao_legislativa', 'composicao_mesa',  'cod_sessao_leg'),

    # parlamentar
    ('parlamentar', 'dependente', 'cod_parlamentar'),
    ('parlamentar', 'filiacao', 'cod_parlamentar'),
    ('parlamentar', 'mandato', 'cod_parlamentar'),
    ('parlamentar', 'composicao_mesa', 'cod_parlamentar'),
    ('parlamentar', 'composicao_comissao', 'cod_parlamentar'),

    # comissao
    ('comissao', 'composicao_comissao', 'cod_comissao'),
    ('periodo_comp_comissao', 'composicao_comissao', 'cod_periodo_comp'),

    # sessao
    ('sessao_plenaria', 'ordem_dia', 'cod_sessao_plen'),
    ('sessao_plenaria', 'expediente_materia', 'cod_sessao_plen'),
    ('sessao_plenaria', 'expediente_sessao_plenaria', 'cod_sessao_plen'),
    ('registro_votacao', 'registro_votacao_parlamentar', 'cod_votacao'),
    # as consultas no código do sapl 2.5
    # votacao_ordem_dia_obter_zsql e votacao_expediente_materia_obter_zsql
    # indicam que os registros de votação de matérias excluídas não são
    # exibidos...
    ('materia_legislativa', 'registro_votacao', 'cod_materia'),
    # as exclusões de registro_votacao sem referência
    # nem a ordem_dia nem a expediente_materia são feitas num método à parte

    # materia
    ('materia_legislativa', 'tramitacao', 'cod_materia'),
    ('materia_legislativa', 'autoria', 'cod_materia'),
    ('materia_legislativa', 'anexada', 'cod_materia_principal'),
    ('materia_legislativa', 'anexada', 'cod_materia_anexada'),
    ('materia_legislativa', 'documento_acessorio', 'cod_materia'),
    ('materia_legislativa', 'numeracao', 'cod_materia'),

    # norma
    ('norma_juridica', 'vinculo_norma_juridica', 'cod_norma_referente'),
    ('norma_juridica', 'vinculo_norma_juridica', 'cod_norma_referida'),

    # documento administrativo
    ('documento_administrativo', 'tramitacao_administrativo', 'cod_documento'),
]


def propaga_exclusoes():
    for tabela_pai, tabela_filha, fk in PROPAGACOES_DE_EXCLUSAO:
        [pk_pai] = get_pk_legado(tabela_pai)
        exec_legado('''
            update {} set ind_excluido = 1 where {} not in (
                select {} from {} where ind_excluido != 1)
            '''.format(tabela_filha, fk, pk_pai, tabela_pai))


def uniformiza_banco():
    exec_legado('SET SESSION sql_mode = "";')  # desliga checagens do mysql

    checa_registros_votacao_ambiguos_e_remove_nao_usados()
    propaga_exclusoes()

    garante_coluna_no_legado('proposicao',
                             'num_proposicao int(11) NULL')

    garante_coluna_no_legado('tipo_materia_legislativa',
                             'ind_num_automatica BOOLEAN NULL DEFAULT FALSE')

    garante_coluna_no_legado('tipo_materia_legislativa',
                             'quorum_minimo_votacao int(11) NULL')

    garante_coluna_no_legado('materia_legislativa',
                             'txt_resultado TEXT NULL')

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


class Record:
    pass


def iter_sql_records(tabela):
    if tabela == 'despacho_inicial':
        sql = ''' select cod_materia, cod_comissao from despacho_inicial
        where ind_excluido <> 1
        group by cod_materia, cod_comissao
        order by cod_materia, min(num_ordem)
        '''
    else:
        sql = 'select * from ' + tabela
        if existe_coluna_no_legado(tabela, 'ind_excluido'):
            sql += ' where ind_excluido <> 1'
    cursor = exec_legado(sql)
    fieldnames = [name[0] for name in cursor.description]
    for row in cursor.fetchall():
        record = Record()
        record.__dict__.update(zip(fieldnames, row))
        yield record


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


def reinicia_sequence(model, id):
    sequence_name = '%s_id_seq' % model._meta.db_table
    exec_sql('ALTER SEQUENCE %s RESTART WITH %s MINVALUE -1;' % (
        sequence_name, id))


REPO = git.Repo.init(DIR_REPO)


def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())


yaml.add_representer(OrderedDict, dict_representer)


# configura timezone de migração
match = re.match('sapl_cm_(.*)', NOME_BANCO_LEGADO)
sigla_casa = match.group(1)
PATH_TABELA_TIMEZONES = DIR_DADOS_MIGRACAO.child('tabela_timezones.yaml')
with open(PATH_TABELA_TIMEZONES, 'r') as arq:
    tabela_timezones = yaml.load(arq)
municipio, uf, nome_timezone = tabela_timezones[sigla_casa]
if nome_timezone:
    timezone = pytz.timezone(nome_timezone)
else:
    timezone = get_timezone(municipio, uf)


def populate_renamed_fields(new, old):
    renames = field_renames[type(new)]

    for field in new._meta.fields:
        old_field_name = renames.get(field.name)
        if old_field_name:
            field_type = field.get_internal_type()

            if field_type == 'ForeignKey':
                fk_field_name = '{}_id'.format(field.name)
                value = get_fk_related(field, old)
                setattr(new, fk_field_name, value)
            else:
                value = getattr(old, old_field_name)

                if (field_type in ['CharField', 'TextField']
                        and value in [None, 'None']):
                    value = ''

                # adiciona timezone faltante aos campos com tempo
                #   os campos TIMESTAMP do mysql são gravados em UTC
                #   os DATETIME e TIME não têm timezone
                def campo_tempo_sem_timezone(tipo):
                    return (field_type == tipo
                            and value and not value.tzinfo)
                if campo_tempo_sem_timezone('DateTimeField'):
                    value = timezone.localize(value)
                if campo_tempo_sem_timezone('TimeField'):
                    value = value.replace(tzinfo=timezone)

                setattr(new, field.name, value)


def roda_comando_shell(cmd):
    res = os.system(cmd)
    assert res == 0, 'O comando falhou: {}'.format(cmd)


def migrar_dados(interativo=True):

    # restaura dump
    arq_dump = Path(DIR_DADOS_MIGRACAO.child(
        'dumps_mysql', '{}.sql'.format(NOME_BANCO_LEGADO)))
    assert arq_dump.exists(), 'Dump do mysql faltando: {}'.format(arq_dump)
    info('Restaurando dump mysql de [{}]'.format(arq_dump))
    normaliza_dump_mysql(arq_dump)
    roda_comando_shell('mysql -uroot < {}'.format(arq_dump))

    # executa ajustes pré-migração, se existirem
    arq_ajustes_pre_migracao = DIR_DADOS_MIGRACAO.child(
        'ajustes_pre_migracao', '{}.sql'.format(sigla_casa))
    if arq_ajustes_pre_migracao.exists():
        exec_legado(arq_ajustes_pre_migracao.read_file())

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
    info('Excluindo entradas antigas do banco destino.')
    call([PROJECT_DIR.child('manage.py'), 'flush',
          '--database=default', '--no-input'], stdout=PIPE)

    # apaga tipos de autor padrão (criados no flush acima)
    TipoAutor.objects.all().delete()

    fill_vinculo_norma_juridica()
    fill_dados_basicos()
    info('Começando migração: ...')
    try:
        ocorrencias.clear()
        migrar_todos_os_models()
    except Exception as e:
        ocorrencias['traceback'] = str(traceback.format_exc())
        raise e
    finally:
        # grava ocorrências
        arq_ocorrencias = Path(REPO.working_dir, 'ocorrencias.yaml')
        with open(arq_ocorrencias, 'w') as arq:
            pyaml.dump(ocorrencias, arq, vspacing=1)
        REPO.git.add([arq_ocorrencias.name])
        info('Ocorrências salvas em\n  {}'.format(arq_ocorrencias))

    # recria tipos de autor padrão que não foram criados pela migração
    cria_models_tipo_autor()


def move_para_depois_de(lista, movido, referencias):
    indice_inicial = lista.index(movido)
    lista.remove(movido)
    indice_apos_refs = max(lista.index(r) for r in referencias) + 1
    lista.insert(max(indice_inicial, indice_apos_refs), movido)
    return lista


def get_models_a_migrar():
    models = [model for app in appconfs for model in app.models.values()
              if model in field_renames]
    # Devido à referência TipoProposicao.tipo_conteudo_related
    # a migração de TipoProposicao precisa ser feita
    # após TipoMateriaLegislativa e TipoDocumento
    # (porém antes de Proposicao)
    move_para_depois_de(models, TipoProposicao,
                        [TipoMateriaLegislativa, TipoDocumento])
    assert models.index(TipoProposicao) < models.index(Proposicao)
    move_para_depois_de(models, Proposicao,
                        [MateriaLegislativa, DocumentoAdministrativo])

    return models


def migrar_todos_os_models():
    for model in get_models_a_migrar():
        migrar_model(model)


def migrar_model(model):
    print('Migrando %s...' % model.__name__)

    model_legado, tabela_legado, campos_pk_legado = \
        get_estrutura_legado(model)

    if len(campos_pk_legado) == 1:
        # a pk no legado tem um único campo
        nome_pk = model_legado._meta.pk.name
        if 'ind_excluido' in {f.name for f in model_legado._meta.fields}:
            # se o model legado tem o campo ind_excluido
            # enumera apenas os não excluídos
            old_records = model_legado.objects.filter(~Q(ind_excluido=1))
        else:
            old_records = model_legado.objects.all()
        old_records = old_records.order_by(nome_pk)

        def get_id_do_legado(old):
            return getattr(old, nome_pk)

        ultima_pk_legado = model_legado.objects.all().aggregate(
            Max('pk'))['pk__max'] or 0
    else:
        # a pk no legado tem mais de um campo
        old_records = iter_sql_records(tabela_legado)
        get_id_do_legado = None
        ultima_pk_legado = model_legado.objects.count()

    ajuste_antes_salvar = AJUSTE_ANTES_SALVAR.get(model)
    ajuste_depois_salvar = AJUSTE_DEPOIS_SALVAR.get(model)

    # convert old records to new ones
    with transaction.atomic():
        novos = []
        sql_delete_legado = ''
        for old in old_records:
            new = model()
            if get_id_do_legado:
                new.id = get_id_do_legado(old)
            try:
                populate_renamed_fields(new, old)
                if ajuste_antes_salvar:
                    ajuste_antes_salvar(new, old)
            except ForeignKeyFaltando as e:
                # tentamos preencher uma FK e o ojeto relacionado
                # não existe
                # então este é um objeo órfão: simplesmente ignoramos
                warn('fk', e.msg, e.dados)
                continue
            else:
                new.clean()  # valida model
                novos.append(new)  # guarda para salvar

                # acumula deleção do registro no legado
                sql_delete_legado += 'delete from {} where {};\n'.format(
                    tabela_legado,
                    ' and '.join(
                        '{} = "{}"'.format(campo,
                                           getattr(old, campo))
                        for campo in campos_pk_legado))

        # salva novos registros
        with reversion.create_revision():
            model.objects.bulk_create(novos)
            reversion.set_comment('Objetos criados pela migração')

        if ajuste_depois_salvar:
            ajuste_depois_salvar()

        # reiniciamos a sequence logo após a última pk do legado
        #
        # É importante que seja do legado (e não da nova base),
        # pois numa nova versão da migração podemos inserir registros
        # não migrados antes sem conflito com pks criadas até lá
        if get_id_do_legado:
            reinicia_sequence(model, ultima_pk_legado + 1)

        # apaga registros migrados do legado
        if sql_delete_legado:
            exec_legado(sql_delete_legado)


# MIGRATION_ADJUSTMENTS #####################################################

def adjust_acompanhamentomateria(new, old):
    new.confirmado = True


NOTA_DOCADM = '''
## NOTA DE MIGRAÇÃO DE DADOS DO SAPL 2.5 ##
O número de protocolo original deste documento era [{num_protocolo}], ano {ano_original}.
'''.strip()  # noqa


def adjust_documentoadministrativo(new, old):
    if old.num_protocolo:
        nota = None
        ano_original = new.ano
        protocolo = Protocolo.objects.filter(
            numero=old.num_protocolo, ano=new.ano)
        if not protocolo:
            # tentamos encontrar o protocolo no ano seguinte
            ano_novo = ano_original + 1
            protocolo = Protocolo.objects.filter(numero=old.num_protocolo,
                                                 ano=ano_novo)
            if protocolo:
                nota = NOTA_DOCADM + '''
O protocolo vinculado é o de mesmo número, porém do ano seguinte ({ano_novo}),
pois não existe protocolo no sistema com este número no ano {ano_original}.
'''
                nota = nota.strip().format(num_protocolo=old.num_protocolo,
                                           ano_original=ano_original,
                                           ano_novo=ano_novo)
                msg = 'PROTOCOLO ENCONTRADO APENAS PARA O ANO SEGUINTE!!!!! '\
                    'DocumentoAdministrativo: {cod_documento}, '\
                    'numero_protocolo: {num_protocolo}, '\
                    'ano doc adm: {ano_original}'
                warn('protocolo_ano_seguinte', msg,
                     {'cod_documento': old.cod_documento,
                      'num_protocolo': old.num_protocolo,
                      'ano_original': ano_original,
                      'nota': nota})
            else:
                nota = NOTA_DOCADM + '''
Não existe no sistema nenhum protocolo com estes dados
e portanto nenhum protocolo foi vinculado a este documento.'''
                nota = nota.format(
                    num_protocolo=old.num_protocolo,
                    ano_original=ano_original)
                msg = 'Protocolo {num_protocolo} faltando (referenciado ' \
                    'no documento administrativo {cod_documento})'
                warn('protocolo_faltando', msg,
                     {'num_protocolo': old.num_protocolo,
                      'cod_documento': old.cod_documento,
                      'nota': nota})
        if protocolo:
            assert len(protocolo) == 1, 'mais de um protocolo encontrado'
            [new.protocolo] = protocolo
        # adiciona nota ao final da observação
        if nota:
            new.observacao += ('\n\n' if new.observacao else '') + nota


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
        warn('ordem_dia_num_ordem_nulo',
             'OrdemDia de PK {pk} tinha numero ordem nulo. '
             'O valor %s foi colocado no lugar.' % new.numero_ordem,
             {'pk': old.pk})


def adjust_parlamentar(new, old):
    if old.ind_unid_deliberativa:
        value = new.unidade_deliberativa
        # Field is defined as not null in legacy db,
        # but data includes null values
        #  => transform None to False
        if value is None:
            warn('unidade_deliberativa_nulo_p_false',
                 'nulo convertido para falso na unidade_deliberativa '
                 'do parlamentar {pk_parlamentar}',
                 {'pk_parlamentar': old.cod_parlamentar})
            new.unidade_deliberativa = False
    # migra município de residência
    if old.cod_localidade_resid:
        municipio_uf = list(exec_legado('''
            select nom_localidade, sgl_uf from localidade
            where cod_localidade = {}'''.format(old.cod_localidade_resid)))
        if municipio_uf:
            new.municipio_residencia, new.uf_residencia = municipio_uf[0]


def adjust_participacao(new, old):
    comissao_id, periodo_id = [
        get_fk_related(Composicao._meta.get_field(name), old)
        for name in ('comissao', 'periodo')]
    with reversion.create_revision():
        composicao, _ = Composicao.objects.get_or_create(
            comissao_id=comissao_id, periodo_id=periodo_id)
        reversion.set_comment('Objeto criado pela migração')
    new.composicao = composicao


def adjust_normarelacionada(new, old):
    new.tipo_vinculo = TipoVinculoNormaJuridica.objects.get(
        sigla=old.tip_vinculo)


def adjust_protocolo_antes_salvar(new, old):
    if new.numero is None:
        new.numero = old.cod_protocolo
        warn('num_protocolo_nulo',
             'Número do protocolo de PK {cod_protocolo} era nulo '
             'e foi alterado para sua pk ({cod_protocolo})',
             {'cod_protocolo': old.cod_protocolo})


def adjust_registrovotacao_antes_salvar(new, old):
    ordem_dia = OrdemDia.objects.filter(
        pk=old.cod_ordem, materia=old.cod_materia)
    expediente_materia = ExpedienteMateria.objects.filter(
        pk=old.cod_ordem, materia=old.cod_materia)

    if ordem_dia and not expediente_materia:
        new.ordem = ordem_dia[0]
    if not ordem_dia and expediente_materia:
        new.expediente = expediente_materia[0]


def adjust_tipoafastamento(new, old):
    assert xor(old.ind_afastamento, old.ind_fim_mandato)
    if old.ind_afastamento:
        new.indicador = 'A'
    elif old.ind_fim_mandato:
        new.indicador = 'F'


def set_generic_fk(new, campo_virtual, old):
    new.content_type = content_types[campo_virtual.related_model]
    new.object_id = get_fk_related(campo_virtual, old)


def adjust_tipoproposicao(new, old):
    "Aponta para o tipo relacionado de matéria ou documento"
    if old.tip_mat_ou_doc:
        campo_virtual = CAMPOS_VIRTUAIS_TIPO_PROPOSICAO[old.ind_mat_ou_doc]
        set_generic_fk(new, campo_virtual, old)


def adjust_proposicao_antes_salvar(new, old):
    if new.data_envio:
        new.ano = new.data_envio.year
    if old.cod_mat_ou_doc:
        tipo_mat_ou_doc = type(new.tipo.tipo_conteudo_related)
        campo_virtual = CAMPOS_VIRTUAIS_PROPOSICAO[tipo_mat_ou_doc]
        set_generic_fk(new, campo_virtual, old)


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


def adjust_normajuridica_depois_salvar():
    # Ajusta relação M2M
    ligacao = NormaJuridica.assuntos.through

    assuntos_migrados, normas_migradas = [
        set(model.objects.values_list('id', flat=True))
        for model in [AssuntoNorma, NormaJuridica]]

    def filtra_assuntos_migrados(cod_assunto):
        return [a for a in map(int, cod_assunto.split(','))
                if a in assuntos_migrados]

    norma_para_assuntos = [
        (norma, filtra_assuntos_migrados(cod_assunto))
        for norma, cod_assunto in OldNormaJuridica.objects.filter(
            pk__in=normas_migradas).values_list('pk', 'cod_assunto')]

    ligacao.objects.bulk_create(
        ligacao(normajuridica_id=norma, assuntonorma_id=assunto)
        for norma, assuntos in norma_para_assuntos
        for assunto in assuntos)


def adjust_autor(new, old):
    # vincula autor com o objeto relacionado, tentando os três campos antigos
    # o primeiro campo preenchido será usado, podendo lançar ForeignKeyFaltando
    for model_relacionado, campo_nome in [(Parlamentar, 'nome_parlamentar'),
                                          (Comissao, 'nome'),
                                          (Partido, 'nome')]:
        field = CAMPOS_VIRTUAIS_AUTOR[model_relacionado]
        fk_encontrada = get_fk_related(field, old)
        if fk_encontrada:
            new.autor_related = model_relacionado.objects.get(id=fk_encontrada)
            new.nome = getattr(new.autor_related, campo_nome)
            break

    if old.col_username:
        user, created = get_user_model().objects.get_or_create(
            username=old.col_username)
        if created:
            # gera uma senha inutilizável, que precisará ser trocada
            user.set_password(None)
            with reversion.create_revision():
                user.save()
                reversion.set_comment(
                    'Usuário criado pela migração para o autor {}'.format(
                        old.cod_autor))
        grupo_autor = Group.objects.get(name="Autor")
        user.groups.add(grupo_autor)
        new.user = user


def adjust_comissao(new, old):
    if not old.dat_extincao and not old.dat_fim_comissao:
        new.ativa = True
    elif (old.dat_extincao and date.today() < new.data_extincao or
          old.dat_fim_comissao and date.today() < new.data_fim_comissao):
        new.ativa = True
    else:
        new.ativa = False


def adjust_tiporesultadovotacao(new, old):
    if 'aprova' in new.nome.lower():
        new.natureza = TipoResultadoVotacao.NATUREZA_CHOICES.aprovado
    elif 'rejeita' in new.nome.lower():
        new.natureza = TipoResultadoVotacao.NATUREZA_CHOICES.rejeitado
    else:
        warn('natureza_desconhecida_tipo_resultadovotacao',
             'Não foi possível identificar a natureza do '
             'tipo de resultado de votação [{pk}: "{nome}"]',
             {'pk': new.pk, 'nome': new.nome})


def remove_style(conteudo):
    if 'style' not in conteudo:
        return conteudo  # atalho que acelera muito os casos sem style

    soup = BeautifulSoup(conteudo, 'html.parser')
    for tag in soup.recursiveChildGenerator():
        if hasattr(tag, 'attrs'):
            tag.attrs = {k: v for k, v in tag.attrs.items() if k != 'style'}
    return str(soup)


def adjust_expediente_sessao(new, old):
    new.conteudo = remove_style(new.conteudo)


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
    TipoResultadoVotacao: adjust_tiporesultadovotacao,
    ExpedienteSessao: adjust_expediente_sessao,
}

AJUSTE_DEPOIS_SALVAR = {
    NormaJuridica: adjust_normajuridica_depois_salvar,
}


# MARCO ######################################################################

TIME_FORMAT = '%H:%M:%S'


# permite a gravação de tempos puros pelo pretty-yaml
def time_representer(dumper, data):
    return dumper.represent_scalar('!time', data.strftime(TIME_FORMAT))


UnsafePrettyYAMLDumper.add_representer(datetime.time, time_representer)


# permite a leitura de tempos puros pelo pyyaml (no padrão gravado acima)
def time_constructor(loader, node):
    value = loader.construct_scalar(node)
    return datetime.datetime.strptime(value, TIME_FORMAT).time()


yaml.add_constructor(u'!time', time_constructor)

TAG_MARCO = 'marco'


def gravar_marco():
    """Grava um dump de todos os dados como arquivos yaml no repo de marco
    """
    # prepara ou localiza repositorio
    dir_dados = Path(REPO.working_dir, 'dados')

    # exporta dados como arquivos yaml
    user_model = get_user_model()
    models = get_models_a_migrar() + [
        Composicao, user_model, Group, ContentType]
    for model in models:
        info('Gravando marco de [{}]'.format(model.__name__))
        dir_model = dir_dados.child(model._meta.app_label, model.__name__)
        dir_model.mkdir(parents=True)
        for data in model.objects.all().values():
            nome_arq = Path(dir_model, '{}.yaml'.format(data['id']))
            with open(nome_arq, 'w') as arq:
                pyaml.dump(data, arq)

    # backup do banco
    print('Gerando backup do banco... ', end='', flush=True)
    arq_backup = DIR_REPO.child('{}.backup'.format(NOME_BANCO_LEGADO))
    arq_backup.remove()
    backup_cmd = '''
        pg_dump --host localhost --port 5432 --username postgres --no-password
        --format custom --blobs --verbose --file {} {}'''.format(
        arq_backup, NOME_BANCO_LEGADO)
    subprocess.check_output(backup_cmd.split(), stderr=subprocess.DEVNULL)
    print('SUCESSO')

    # salva mudanças
    REPO.git.add([dir_dados.name])
    if 'master' not in REPO.heads or REPO.index.diff('HEAD'):
        # se de fato existe mudança
        REPO.index.commit('Grava marco')
    REPO.git.execute('git tag -f'.split() + [TAG_MARCO])
