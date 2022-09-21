import datetime
import json
import os
import re
import subprocess
import traceback
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import date
from functools import lru_cache, partial
from itertools import groupby
from operator import xor
from typing import Type, Union

import git
import pkg_resources
import pyaml
import pytz
import reversion
import sapl.legacy.models as legacy_models
import yaml
from bs4 import BeautifulSoup
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import connections, transaction
from django.db.models import Field, Max, Model, Q
from pyaml import UnsafePrettyYAMLDumper
from reversion.models import Revision, Version
from sapl.base.models import AppConfig as AppConf
from sapl.base.models import Autor, TipoAutor
from sapl.base.receivers import cria_models_tipo_autor
from sapl.comissoes.models import Comissao, Composicao, Participacao, Reuniao
from sapl.legacy.models import NormaJuridica as OldNormaJuridica
from sapl.legacy.models import TipoNumeracaoProtocolo
from sapl.legacy_migration_settings import (
    DIR_DADOS_MIGRACAO,
    DIR_REPO,
    NOME_BANCO_LEGADO,
    PYTZ_TIMEZONE,
    SIGLA_CASA,
)
from sapl.materia.models import (
    AcompanhamentoMateria,
    DocumentoAcessorio,
    MateriaLegislativa,
    Proposicao,
    StatusTramitacao,
    TipoDocumento,
    TipoMateriaLegislativa,
    TipoProposicao,
    Tramitacao,
)
from sapl.norma.models import (
    AssuntoNorma,
    NormaJuridica,
    NormaRelacionada,
    TipoVinculoNormaJuridica,
)
from sapl.parlamentares.models import (
    ComposicaoMesa,
    Legislatura,
    Mandato,
    MesaDiretora,
    Parlamentar,
    Partido,
    SessaoLegislativa,
    TipoAfastamento,
)
from sapl.protocoloadm.models import (
    DocumentoAdministrativo,
    Protocolo,
    StatusTramitacaoAdministrativo,
)
from sapl.sessao.models import (
    ExpedienteMateria,
    ExpedienteSessao,
    OrdemDia,
    RegistroVotacao,
    TipoResultadoVotacao,
)
from sapl.utils import normalize
from unipath import Path

from .scripts.normaliza_dump_mysql import normaliza_dump_mysql

# BASE ######################################################################
#  apps to be migrated, in app dependency order (very important)
appconfs = [
    apps.get_app_config(n)
    for n in [
        "parlamentares",
        "comissoes",
        # base precisa vir depois dos apps parlamentares e comissoes
        # pois Autor os referencia
        "base",
        "materia",
        "norma",
        "sessao",
        "lexml",
        "protocoloadm",
    ]
]

unique_constraints = []
one_to_one_constraints = []
primeira_vez = []

# apps quase não têm interseção
name_sets = [(ac.label, set(m.__name__ for m in ac.get_models())) for ac in appconfs]
for a1, s1 in name_sets:
    for a2, s2 in name_sets:
        if a1 is not a2:
            # existe uma interseção de nomes entre comissoes e materia
            if {a1, a2} == {"comissoes", "materia"}:
                assert s1.intersection(s2) == {"DocumentoAcessorio"}
            else:
                assert not s1.intersection(s2)


# RENAMES ###################################################################

MODEL_RENAME_PATTERN = re.compile(r"(.+) \((.+)\)")
MODEL_RENAME_INCLUDE_PATTERN = re.compile("<(.+)>")


ModelType = Type[Model]


def get_renames():
    field_renames: dict[ModelType, dict[str, str]] = {}
    model_renames: dict[ModelType, str] = {}
    includes = {}
    for app in appconfs:
        app_rename_data = yaml.safe_load(
            pkg_resources.resource_string(app.module.__name__, "legacy.yaml")  # type: ignore
        )
        for model_name, renames in app_rename_data.items():
            # armazena ou substitui includes
            if MODEL_RENAME_INCLUDE_PATTERN.match(model_name):
                includes[model_name] = renames
                continue
            elif isinstance(renames, str):
                renames = includes[renames]
            # detecta mudança de nome
            match = MODEL_RENAME_PATTERN.match(model_name)
            if match:
                model_name, old_name = match.groups()
            else:
                old_name = None
            model = app.get_model(model_name)
            if old_name:
                model_renames[model] = old_name
            field_renames[model] = renames

    return field_renames, model_renames


field_renames, model_renames = get_renames()
legacy_app = apps.get_app_config("legacy")
models_novos_para_antigos: dict[ModelType, ModelType] = {
    model: legacy_app.get_model(model_renames.get(model, model.__name__))
    for model in field_renames
}
models_novos_para_antigos[Composicao] = models_novos_para_antigos[Participacao]


@dataclass(frozen=True)
class CampoVirtual:
    model: ModelType
    related_model: ModelType
    null = True


campos_novos_para_antigos: dict[Union[Field, CampoVirtual], str] = {
    model._meta.get_field(nome_novo): nome_antigo
    for model, renames in field_renames.items()
    for nome_novo, nome_antigo in renames.items()
}

# campos de Composicao (de Comissao)
for nome_novo, nome_antigo in (
    ("comissao", "cod_comissao"),
    ("periodo", "cod_periodo_comp"),
):
    campos_novos_para_antigos[Composicao._meta.get_field(nome_novo)] = nome_antigo


# campos virtuais de Proposicao para funcionar com get_fk_related
CAMPOS_VIRTUAIS_PROPOSICAO = {
    TipoMateriaLegislativa: CampoVirtual(Proposicao, MateriaLegislativa),
    TipoDocumento: CampoVirtual(Proposicao, DocumentoAcessorio),
}
for campo_virtual in CAMPOS_VIRTUAIS_PROPOSICAO.values():
    campos_novos_para_antigos[campo_virtual] = "cod_mat_ou_doc"


CAMPOS_VIRTUAIS_TIPO_PROPOSICAO = {
    "M": CampoVirtual(TipoProposicao, TipoMateriaLegislativa),
    "D": CampoVirtual(TipoProposicao, TipoDocumento),
}
for campo_virtual in CAMPOS_VIRTUAIS_TIPO_PROPOSICAO.values():
    campos_novos_para_antigos[campo_virtual] = "tip_mat_ou_doc"


# campos virtuais de Autor para funcionar com get_fk_related
CAMPOS_VIRTUAIS_AUTOR = {
    related: CampoVirtual(Autor, related)
    for related in (Parlamentar, Comissao, Partido)
}
for related, campo_antigo in [
    (Parlamentar, "cod_parlamentar"),
    (Comissao, "cod_comissao"),
    (Partido, "cod_partido"),
]:
    campo_virtual = CAMPOS_VIRTUAIS_AUTOR[related]
    campos_novos_para_antigos[campo_virtual] = campo_antigo


# MIGRATION #################################################################


def info(msg):
    print("INFO: " + msg)


ocorrencias = defaultdict(list)


def warn(tipo, msg, dados):
    ocorrencias[tipo].append(dados)
    print("CUIDADO! " + msg.format(**dados))


@lru_cache()
def get_pk_legado(tabela: str) -> tuple[str, ...]:
    if tabela == "despacho_inicial":
        # adaptação para deleção correta no mysql ao final de migrar_model
        # acompanha o agrupamento de despacho_inicial feito em iter_sql_records
        return "cod_materia", "cod_comissao"
    elif tabela == "mesa_sessao_plenaria":
        # retiramos 'cod_sessao_leg' redundante que da problema
        # ao verificar se o registro já está migrado
        return "cod_cargo", "cod_parlamentar", "cod_sessao_plen"
    elif tabela == "composicao_mesa":
        # em alguns bancos a chave é
        # cod_parlamentar, cod_periodo_comp, cod_cargo
        # mas essa parece sempre ser uma chave candidata
        return "cod_parlamentar", "cod_sessao_leg", "cod_cargo"
    res = exec_legado('show index from {} WHERE Key_name = "PRIMARY"'.format(tabela))
    return [r[4] for r in res]  # type: ignore


@lru_cache()
def get_estrutura_legado(model: ModelType) -> tuple[ModelType, str, tuple[str]]:
    model_legado = models_novos_para_antigos[model]
    tabela_legado = model_legado._meta.db_table
    campos_pk_legado = get_pk_legado(tabela_legado)
    return model_legado, tabela_legado, campos_pk_legado


def com_aspas_se_necessario(valor):
    if isinstance(valor, int):
        return valor
    else:
        return '"{}"'.format(valor)


class ForeignKeyFaltando(ObjectDoesNotExist):
    "Uma FK aponta para um registro inexistente"

    def __init__(self, field, valor, old):
        self.field = field
        self.valor = valor
        self.old = old

    msg = "FK não encontrada para [{campo} = {valor}] (em {tabela} / pk = {pk})"  # noqa

    @property
    def dados(self):
        campo = campos_novos_para_antigos[self.field]
        _, tabela, campos_pk = get_estrutura_legado(self.field.model)
        pk = {c: getattr(self.old, c) for c in campos_pk}
        sql = "select * from {} where {};".format(
            tabela,
            " and ".join(
                ["{} = {}".format(k, com_aspas_se_necessario(v)) for k, v in pk.items()]
            ),
        )
        return OrderedDict(
            (
                ("campo", campo),
                ("valor", self.valor),
                ("tabela", tabela),
                ("pk", pk),
                ("sql", sql),
            )
        )


def get_all_ids_from_model(model):
    return set(model.objects.values_list("id", flat=True))


@lru_cache()
def _cached_get_all_ids_from_model(model):
    # esta função para uso apenas em get_fk_related
    return get_all_ids_from_model(model)


def get_fk_related(field, old):
    valor = getattr(old, campos_novos_para_antigos[field])
    if valor is None and field.null:
        return None
    if valor in _cached_get_all_ids_from_model(field.related_model):
        return valor
    elif valor == 0 and field.null:
        # consideramos zeros como nulos, se não está entre os ids anteriores
        return None
    else:
        raise ForeignKeyFaltando(field=field, valor=valor, old=old)


def exec_sql(sql, db="default"):
    cursor = connections[db].cursor()
    cursor.execute(sql)
    return cursor


exec_legado = partial(exec_sql, db="legacy")


def formatar_lista_para_sql(iteravel):
    lista = list(iteravel)
    if lista:
        return "({})".format(str(lista)[1:-1])  # transforma "[...]" em "(...)"
    else:
        return None


def exec_legado_em_subconjunto(sql, ids):
    """Executa uma query sql no legado no formato '.... in {}'
    interpolando `ids`, se houver ids"""

    lista_sql = formatar_lista_para_sql(ids)
    if lista_sql:
        return exec_legado(sql.format(lista_sql))
    else:
        return []


def primeira_coluna(cursor):
    return (r[0] for r in cursor)


# UNIFORMIZAÇÃO DO BANCO ANTES DA MIGRAÇÃO ###############################

SQL_NAO_TEM_TABELA = """
   SELECT count(*)
   FROM information_schema.columns
   WHERE table_schema=database()
     AND TABLE_NAME="{}"
"""


def existe_tabela_no_legado(tabela):
    sql = SQL_NAO_TEM_TABELA.format(tabela)
    return list(primeira_coluna(exec_legado(sql)))[0]


def existe_coluna_no_legado(tabela, coluna):
    sql_nao_tem_coluna = SQL_NAO_TEM_TABELA + ' AND COLUMN_NAME="{}"'
    sql = sql_nao_tem_coluna.format(tabela, coluna)
    return list(primeira_coluna(exec_legado(sql)))[0] > 0


def garante_coluna_no_legado(tabela, spec_coluna):
    spec_coluna = spec_coluna.strip().replace("`", "")
    coluna = spec_coluna.split()[0]
    if not existe_coluna_no_legado(tabela, coluna):
        exec_legado("ALTER TABLE {} ADD COLUMN {}".format(tabela, spec_coluna))
    assert existe_coluna_no_legado(tabela, coluna)


def garante_tabela_no_legado(create_table):
    tabela = create_table.strip().splitlines()[0].split()[2]
    if not existe_tabela_no_legado(tabela):
        exec_legado(create_table)
        assert existe_tabela_no_legado(tabela)


TABELAS_REFERENCIANDO_AUTOR = [
    # <nome da tabela>, <tem ind excluido>
    ("autoria", True),
    ("documento_administrativo", True),
    ("proposicao", True),
    ("protocolo", False),
]


def reverte_exclusao_de_autores_referenciados_no_legado():
    """Reverte a exclusão de autores que sejam referenciados de alguma forma
    na base legada"""

    def get_autores_referenciados(tabela, tem_ind_excluido):
        sql = """select distinct cod_autor from {}
                 where cod_autor is not null
              """.format(
            tabela
        )
        if tem_ind_excluido:
            sql += " and ind_excluido != 1"
        return primeira_coluna(exec_legado(sql))

    # reverte exclusões de autores referenciados por outras tabelas
    autores_referenciados = {
        cod
        for tabela, tem_ind_excluido in TABELAS_REFERENCIANDO_AUTOR
        for cod in get_autores_referenciados(tabela, tem_ind_excluido)
    }
    exec_legado_em_subconjunto(
        "update autor set ind_excluido = 0 where cod_autor in {}",
        autores_referenciados,
    )

    # propaga exclusões para autores não referenciados
    for tabela, fk in [
        ("parlamentar", "cod_parlamentar"),
        ("comissao", "cod_comissao"),
    ]:
        sql = """
            update autor set ind_excluido = 1
            where {cod_parlamentar} is not null
            and {cod_parlamentar} not in (
                select {cod_parlamentar} from {parlamentar}
                where ind_excluido <> 1)
            """.format(
            parlamentar=tabela, cod_parlamentar=fk
        )
        if autores_referenciados:
            sql += " and cod_autor not in ({})".format(
                ", ".join(map(str, autores_referenciados))
            )
        exec_legado(sql)


def get_reapontamento_de_autores_repetidos(autores):
    """Dada uma lista ordenada de pares (cod_zzz, cod_autor) retorna:

    * a lista de grupos de cod_autor'es repetidos
      (quando há mais de um cod_autor para um mesmo cod_zzz)

    * a lista de cod_autor'es a serem apagados (todos além do 1o de cada grupo)
    """
    grupos_de_repetidos = [
        [cod_autor for _, cod_autor in grupo]
        for cod_zzz, grupo in groupby(autores, lambda r: r[0])
    ]
    # mantém apenas os grupos com mais de um autor por cod_zzz
    grupos_de_repetidos = [g for g in grupos_de_repetidos if len(g) > 1]
    # aponta cada autor de cada grupo de repetidos para o 1o do seu grupo
    reapontamento = {
        autor: grupo[0] for grupo in grupos_de_repetidos for autor in grupo
    }
    # apagaremos todos menos o primeiro
    apagar = [k for k, v in reapontamento.items() if k != v]
    return reapontamento, apagar


def get_autorias_sem_repeticoes(autoria, reapontamento):
    "Autorias sem repetições de autores e com ind_primeiro_autor ajustado"

    # substitui cada autor repetido pelo 1o de seu grupo
    autoria = sorted((reapontamento[a], m, i) for a, m, i in autoria)
    # agrupa por [autor (1o do grupo de repetidos), materia], com
    # ind_primeiro_autor == 1 se isso acontece em qualquer autor do grupo
    autoria = [
        (a, m, max(i for a, m, i in grupo))
        for (a, m), grupo in groupby(autoria, lambda x: x[:2])
    ]
    return autoria


def unifica_autores_repetidos_no_legado(campo_agregador):
    "Reúne autores repetidos em um único, antes da migracão"

    # usamos uma tupla neutra se o conjunto é vazio
    # p q a query seja sintaticamente correta
    ids_ja_migrados = formatar_lista_para_sql(get_all_ids_from_model(Autor) or [-1000])

    # enumeramos a repeticoes segundo o campo relevante
    # (p. ex. cod_parlamentar ou cod_comissao)
    # a ordenação prioriza, as entradas:
    #  - ja migradas previamente
    #  - não excluidas,
    #  - em seguida as que têm col_username,
    #  - em seguida as que têm des_cargo
    autores = exec_legado(
        f"""
        select {campo_agregador}, cod_autor,
        (cod_autor in {ids_ja_migrados}) ja_migrado
        from autor
        where {campo_agregador} is not null
        order by {campo_agregador},
        ja_migrado desc,
        ind_excluido, col_username desc, des_cargo desc"""
    )
    # descartamos o último campo, usado apenas p ordenar corretamente
    autores = [a[:-1] for a in autores]
    # ordenamos, pois o order by nesses instalações do mysql parece ignorar case
    # em alguns acasos temos erros estranhos
    autores = sorted(autores)

    reapontamento, apagar = get_reapontamento_de_autores_repetidos(autores)

    # se não houver autores repetidos encerramos por aqui
    if not reapontamento:
        return

    # Reaponta AUTORIA (many-to-many)

    # simplificamos retirando inicialmente as autorias excluidas
    exec_legado("delete from autoria where ind_excluido = 1")

    # selecionamos as autorias envolvidas em repetições de autores
    from_autoria = " from autoria where cod_autor in {}"
    autoria = exec_legado_em_subconjunto(
        "select cod_autor, cod_materia, ind_primeiro_autor" + from_autoria,
        reapontamento,
    )

    # apagamos todas as autorias envolvidas
    exec_legado_em_subconjunto("delete " + from_autoria, reapontamento)
    # e depois inserimos apenas as sem repetições c ind_primeiro_autor ajustado
    nova_autoria = get_autorias_sem_repeticoes(autoria, reapontamento)
    if nova_autoria:
        exec_legado(
            """
            insert into autoria
            (cod_autor, cod_materia, ind_primeiro_autor, ind_excluido)
            values {}""".format(
                ", ".join([str((a, m, i, 0)) for a, m, i in nova_autoria])
            )
        )

    # Reaponta outras tabelas que referenciam autor
    for tabela, _ in TABELAS_REFERENCIANDO_AUTOR:
        for antigo, novo in reapontamento.items():
            if antigo != novo:
                exec_legado(
                    """
                    update {} set cod_autor = {} where cod_autor = {}
                    """.format(
                        tabela, novo, antigo
                    )
                )

    # Finalmente excluimos os autores redundantes,
    # cujas referências foram todas substituídas a essa altura
    exec_legado_em_subconjunto("delete from autor where cod_autor in {}", apagar)


def anula_tipos_origem_externa_invalidos():
    """Anula tipos de origem externa inválidos
    para que não impeçam a migração da matéria"""

    tipos_validos = primeira_coluna(
        exec_legado(
            """
        select tip_materia
        from tipo_materia_legislativa
        where ind_excluido <> 1;"""
        )
    )

    exec_legado_em_subconjunto(
        """
        update materia_legislativa
        set tip_origem_externa = NULL
        where tip_origem_externa not in {};""",
        tipos_validos,
    )


def get_ids_registros_votacao_para(tabela):
    sql = """
        select r.cod_votacao from {} o
            inner join registro_votacao r on
            o.cod_ordem = r.cod_ordem and o.cod_materia = r.cod_materia
        where o.ind_excluido != 1 and r.ind_excluido != 1
        order by o.cod_sessao_plen, num_ordem
        """.format(
        tabela
    )
    return set(primeira_coluna(exec_legado(sql)))


def checa_registros_votacao_ambiguos_e_remove_nao_usados():
    """Interrompe a migração caso restem registros de votação
    que apontam para uma ordem_dia e um expediente_materia ao mesmo tempo.

    Remove do legado registros de votação que não têm
    nem ordem_dia nem expediente_materia associados."""

    ordem, expediente = [
        get_ids_registros_votacao_para(tabela)
        for tabela in ("ordem_dia", "expediente_materia")
    ]

    # interrompe migração se houver registros ambíguos
    ambiguos = ordem.intersection(expediente)
    como_resolver = get_como_resolver_registro_votacao_ambiguo()
    ambiguos = ambiguos - set(como_resolver)

    if ambiguos:
        warn(
            "registro_votacao_ambiguos",
            "Existe(m) RegistroVotacao ambíguo(s): {cod_votacao}",
            {"cod_votacao": ambiguos},
        )

    # exclui registros não usados (zumbis)
    todos = set(
        primeira_coluna(exec_legado("select cod_votacao from registro_votacao"))
    )
    nao_usados = todos - ordem.union(expediente)
    exec_legado_em_subconjunto(
        """
        update registro_votacao set ind_excluido = 1
        where cod_votacao in {}""",
        nao_usados,
    )


PROPAGACOES_DE_EXCLUSAO = [
    # sessao_legislativa
    ("sessao_legislativa", "composicao_mesa", "cod_sessao_leg"),
    # parlamentar
    ("parlamentar", "dependente", "cod_parlamentar"),
    ("parlamentar", "filiacao", "cod_parlamentar"),
    ("parlamentar", "mandato", "cod_parlamentar"),
    ("parlamentar", "composicao_mesa", "cod_parlamentar"),
    ("parlamentar", "composicao_comissao", "cod_parlamentar"),
    # no 2.5 os parlamentares excluídos não são listados na presença da sessão
    ("parlamentar", "sessao_plenaria_presenca", "cod_parlamentar"),
    # ... nem na presença da ordem do dia
    ("parlamentar", "ordem_dia_presenca", "cod_parlamentar"),
    # ... nem na mesa da sessão
    ("parlamentar", "mesa_sessao_plenaria", "cod_parlamentar"),
    # coligacao
    ("coligacao", "composicao_coligacao", "cod_coligacao"),
    # comissao
    ("comissao", "composicao_comissao", "cod_comissao"),
    ("periodo_comp_comissao", "composicao_comissao", "cod_periodo_comp"),
    # sessao
    ("sessao_plenaria", "ordem_dia", "cod_sessao_plen"),
    ("sessao_plenaria", "expediente_materia", "cod_sessao_plen"),
    ("sessao_plenaria", "expediente_sessao_plenaria", "cod_sessao_plen"),
    ("sessao_plenaria", "sessao_plenaria_presenca", "cod_sessao_plen"),
    ("sessao_plenaria", "ordem_dia_presenca", "cod_sessao_plen"),
    ("sessao_plenaria", "mesa_sessao_plenaria", "cod_sessao_plen"),
    ("sessao_plenaria", "oradores", "cod_sessao_plen"),
    ("sessao_plenaria", "oradores_expediente", "cod_sessao_plen"),
    # as consultas no código do sapl 2.5
    # votacao_ordem_dia_obter_zsql e votacao_expediente_materia_obter_zsql
    # indicam que os registros de votação de matérias excluídas não são
    # exibidos...
    ("materia_legislativa", "registro_votacao", "cod_materia"),
    # as exclusões de registro_votacao sem referência
    # nem a ordem_dia nem a expediente_materia são feitas num método à parte
    # materia
    ("materia_legislativa", "tramitacao", "cod_materia"),
    ("materia_legislativa", "autoria", "cod_materia"),
    ("materia_legislativa", "anexada", "cod_materia_principal"),
    ("materia_legislativa", "anexada", "cod_materia_anexada"),
    ("materia_legislativa", "documento_acessorio", "cod_materia"),
    ("materia_legislativa", "numeracao", "cod_materia"),
    ("materia_legislativa", "expediente_materia", "cod_materia"),
    ("materia_legislativa", "ordem_dia", "cod_materia"),
    ("materia_legislativa", "acomp_materia", "cod_materia"),
    ("materia_legislativa", "despacho_inicial", "cod_materia"),
    ("materia_legislativa", "legislacao_citada", "cod_materia"),
    ("materia_legislativa", "relatoria", "cod_materia"),
    ("materia_legislativa", "materia_assunto", "cod_materia"),
    # norma
    ("norma_juridica", "vinculo_norma_juridica", "cod_norma_referente"),
    ("norma_juridica", "vinculo_norma_juridica", "cod_norma_referida"),
    ("norma_juridica", "legislacao_citada", "cod_norma"),
    # documento administrativo
    ("documento_administrativo", "tramitacao_administrativo", "cod_documento"),
]

PROPAGACOES_DE_EXCLUSAO_REGISTROS_VOTACAO = [
    ("registro_votacao", "registro_votacao_parlamentar", "cod_votacao")
]


def propaga_exclusoes(propagacoes):
    for tabela_pai, tabela_filha, fk in propagacoes:
        [pk_pai] = get_pk_legado(tabela_pai)
        sql = """
            update {} set ind_excluido = 1 where {} not in (
                select {} from {} where ind_excluido != 1)
            """.format(
            tabela_filha, fk, pk_pai, tabela_pai
        )
        exec_legado(sql)


def corrige_unidades_tramitacao_destino_vazia_como_anterior():
    """Se uma unidade de tramitação estiver vazia no legado a configura
    como a anterior"""

    for tabela_tramitacao in ["tramitacao", "tramitacao_administrativo"]:
        exec_legado(
            """
            update {}
            set cod_unid_tram_dest = cod_unid_tram_local
            where cod_unid_tram_dest is null;
            """.format(
                tabela_tramitacao
            )
        )


def apaga_ref_a_mats_e_docs_inexistentes_em_proposicoes():
    # as referencias a matérias e documentos apagados não aparecem no 3.1
    # além do que, se ressuscitássemos essas matérias e docs,
    # não seria possível apagá-los,
    # pois é impossível para um usuário não autor acessar as proposicões
    # para apagar a referências antes
    exec_legado(
        """
        update proposicao set cod_materia = NULL where cod_materia not in (
            select cod_materia from materia_legislativa
            where ind_excluido <> 1);
    """
    )
    props_sem_mats = list(
        primeira_coluna(
            exec_legado(
                """
        select cod_proposicao from proposicao p inner join tipo_proposicao t
        on p.tip_proposicao = t.tip_proposicao
        where t.ind_mat_ou_doc = 'M' and cod_mat_ou_doc not in (
            select cod_materia from materia_legislativa
            where ind_excluido <> 1)
        """
            )
        )
    )
    props_sem_docs = list(
        primeira_coluna(
            exec_legado(
                """
        select cod_proposicao from proposicao p inner join tipo_proposicao t
        on p.tip_proposicao = t.tip_proposicao
        where t.ind_mat_ou_doc = 'D' and cod_mat_ou_doc not in (
            select cod_documento from documento_acessorio
            where ind_excluido <> 1);
        """
            )
        )
    )
    exec_legado_em_subconjunto(
        """
        update proposicao set cod_mat_ou_doc = NULL
        where cod_proposicao in {}""",
        props_sem_mats + props_sem_docs,
    )


def reaponta_tipo_autor():
    # e corrige um erro comum
    if TipoAutor.objects.filter(descricao="Comissão").exists():
        exec_legado(
            """  update tipo_autor set des_tipo_autor = 'Comissão'
                 where des_tipo_autor = 'Comissao';
            """
        )

    conflitos, max_id = encontra_conflitos_tipo_autor()

    def sql_reaponta_tipo_autor(id_novo, id_antigo):
        return f"""
    update tipo_autor set tip_autor = {id_novo} where tip_autor = {id_antigo};
    update autor set tip_autor = {id_novo} where tip_autor = {id_antigo};
            """

    # tenta reapontar para o que é usado agora
    conflitos_restantes = []
    for id_antigo, (descricao_no_legado, *_) in conflitos.items():
        tipo_novo = TipoAutor.objects.filter(descricao=descricao_no_legado)
        if tipo_novo:
            [tipo_novo] = tipo_novo
            id_novo = tipo_novo.id
            exec_legado(sql_reaponta_tipo_autor(id_novo, id_antigo))
        else:
            conflitos_restantes.append(id_antigo)

    # reaponta para novos ids
    for id_novo, id_antigo in enumerate(conflitos_restantes, max_id + 1):
        exec_legado(sql_reaponta_tipo_autor(id_novo, id_antigo))


def uniformiza_banco(primeira_migracao):
    "Uniformiza e ajusta o banco legado antes de migrar"

    # restringe TipoAutor somente ao realmente utilizado
    exec_legado(
        """  delete from tipo_autor where tip_autor not in (
             select distinct(tip_autor) from autor);
        """
    )
    if not primeira_migracao:
        reaponta_tipo_autor()

    propaga_exclusoes(PROPAGACOES_DE_EXCLUSAO)
    checa_registros_votacao_ambiguos_e_remove_nao_usados()
    propaga_exclusoes(PROPAGACOES_DE_EXCLUSAO_REGISTROS_VOTACAO)

    garante_coluna_no_legado("proposicao", "num_proposicao int(11) NULL")

    garante_coluna_no_legado(
        "tipo_materia_legislativa", "ind_num_automatica BOOLEAN NULL DEFAULT FALSE"
    )

    garante_coluna_no_legado(
        "tipo_materia_legislativa", "quorum_minimo_votacao int(11) NULL"
    )

    garante_coluna_no_legado("materia_legislativa", "txt_resultado TEXT NULL")

    # Cria campos cod_presenca_sessao (sendo a nova PK da tabela)
    # e dat_sessao em sessao_plenaria_presenca
    if not existe_coluna_no_legado("sessao_plenaria_presenca", "cod_presenca_sessao"):
        exec_legado(
            """
            ALTER TABLE sessao_plenaria_presenca
            DROP PRIMARY KEY,
            ADD cod_presenca_sessao INT auto_increment PRIMARY KEY FIRST;
        """
        )
        assert existe_coluna_no_legado(
            "sessao_plenaria_presenca", "cod_presenca_sessao"
        )

    garante_coluna_no_legado("sessao_plenaria_presenca", "dat_sessao DATE NULL")

    garante_tabela_no_legado(
        """
        CREATE TABLE lexml_registro_publicador (
            cod_publicador INT auto_increment NOT NULL,
            id_publicador INT, nom_publicador varchar(255),
            adm_email varchar(50),
            sigla varchar(255),
            nom_responsavel varchar(255),
            tipo varchar(50),
            id_responsavel INT, PRIMARY KEY (cod_publicador));
    """
    )

    garante_tabela_no_legado(
        """
        CREATE TABLE lexml_registro_provedor (
            cod_provedor INT auto_increment NOT NULL,
            id_provedor INT, nom_provedor varchar(255),
            sgl_provedor varchar(15),
            adm_email varchar(50),
            nom_responsavel varchar(255),
            tipo varchar(50),
            id_responsavel INT, xml_provedor longtext,
            PRIMARY KEY (cod_provedor));
    """
    )

    garante_tabela_no_legado(
        """
        CREATE TABLE tipo_situacao_militar (
            tip_situacao_militar INT auto_increment NOT NULL,
            des_tipo_situacao varchar(50),
            ind_excluido INT, PRIMARY KEY (tip_situacao_militar));
    """
    )

    update_specs = """
vinculo_norma_juridica   | ind_excluido = ''           | trim(ind_excluido) = '0'
unidade_tramitacao       | cod_parlamentar = NULL      | cod_parlamentar = 0
parlamentar              | cod_nivel_instrucao = NULL  | cod_nivel_instrucao = 0
parlamentar              | tip_situacao_militar = NULL | tip_situacao_militar = 0
mandato                  | tip_afastamento = NULL      | tip_afastamento = 0
relatoria                | tip_fim_relatoria = NULL    | tip_fim_relatoria = 0
sessao_plenaria_presenca | dat_sessao = NULL           | dat_sessao = 0
    """.strip().splitlines()

    for spec in update_specs:
        spec = spec.split("|")
        exec_legado("UPDATE {} SET {} WHERE {}".format(*spec))

    # retira apontamentos de materia para assunto inexistente
    exec_legado("delete from materia_assunto where cod_assunto = 0")

    # corrige string "None" em autor
    exec_legado('update autor set des_cargo = NULL where des_cargo = "None"')

    unifica_autores_repetidos_no_legado("cod_parlamentar")
    unifica_autores_repetidos_no_legado("cod_comissao")
    unifica_autores_repetidos_no_legado("col_username")

    # é importante reverter a exclusão de autores somente depois, para que a
    # unificação possa dar prioridade às informações dos autores não excluídos
    reverte_exclusao_de_autores_referenciados_no_legado()

    anula_tipos_origem_externa_invalidos()
    corrige_unidades_tramitacao_destino_vazia_como_anterior()

    # matérias inexistentes não são mostradas em norma jurídica => apagamos
    exec_legado(
        """update norma_juridica set cod_materia = NULL
        where cod_materia not in (
            select cod_materia from materia_legislativa
            where ind_excluido <> 1);"""
    )

    apaga_ref_a_mats_e_docs_inexistentes_em_proposicoes()


class Record:
    pass


def iter_sql_records(tabela):
    if tabela == "despacho_inicial":
        sql = """ select cod_materia, cod_comissao from despacho_inicial
        where ind_excluido <> 1
        group by cod_materia, cod_comissao
        order by cod_materia, min(num_ordem)
        """
    else:
        sql = "select * from " + tabela
        if existe_coluna_no_legado(tabela, "ind_excluido"):
            sql += " where ind_excluido <> 1"
    cursor = exec_legado(sql)
    fieldnames = [name[0] for name in cursor.description]
    for row in cursor.fetchall():
        record = Record()
        record.__dict__.update(zip(fieldnames, row))
        yield record


def fill_vinculo_norma_juridica():
    lista = [
        ("A", "Altera o(a)", "Alterado(a) pelo(a)"),
        ("R", "Revoga integralmente o(a)", "Revogado(a) integralmente pelo(a)"),
        ("P", "Revoga parcialmente o(a)", "Revogado(a) parcialmente pelo(a)"),
        (
            "T",
            "Revoga integralmente por consolidação",
            "Revogado(a) integralmente por consolidação",
        ),
        ("C", "Norma correlata", "Norma correlata"),
        ("S", "Ressalva o(a)", "Ressalvada pelo(a)"),
        ("E", "Reedita o(a)", "Reeditada pelo(a)"),
        ("I", "Reedita com alteração o(a)", "Reeditada com alteração pelo(a)"),
        ("G", "Regulamenta o(a)", "Regulamentada pelo(a)"),
        ("K", "Suspende parcialmente o(a)", "Suspenso(a) parcialmente pelo(a)"),
        ("L", "Suspende integralmente o(a)", "Suspenso(a) integralmente pelo(a)"),
        (
            "N",
            "Julga integralmente inconstitucional",
            "Julgada integralmente inconstitucional",
        ),
        (
            "O",
            "Julga parcialmente inconstitucional",
            "Julgada parcialmente inconstitucional",
        ),
    ]
    lista_objs = [
        TipoVinculoNormaJuridica(
            sigla=item[0], descricao_ativa=item[1], descricao_passiva=item[2]
        )
        for item in lista
    ]
    TipoVinculoNormaJuridica.objects.bulk_create(lista_objs)


def criar_configuracao_inicial():
    # só deve ser chamado na primeira migracão
    appconf = AppConf.objects.first()
    if appconf:
        appconf.delete()
        assert not AppConf.objects.exists()

    # Ajusta sequencia numérica de protocolo e cria base.AppConfig
    if (
        existe_tabela_no_legado(TipoNumeracaoProtocolo._meta.db_table)
        and TipoNumeracaoProtocolo.objects.exists()
    ):
        # se este banco legado tem a a configuração de numeração de protocolo
        tipo = TipoNumeracaoProtocolo.objects.latest("dat_inicial_protocolo")
        descricao = tipo.des_numeracao_protocolo
        if "POR ANO" in descricao:
            sequencia_numeracao = "A"
        elif "POR LEGISLATURA" in descricao:
            sequencia_numeracao = "L"
        elif "CONSECUTIVO" in descricao:
            sequencia_numeracao = "U"
    else:
        sequencia_numeracao = "A"
    appconf = AppConf(sequencia_numeracao_protocolo=sequencia_numeracao)  # type: ignore
    appconf.save()


def get_sequence_name_and_last_value(model):
    sequence_name = "%s_id_seq" % model._meta.db_table
    [(last_value,)] = exec_sql(f"select last_value from {sequence_name}")
    return sequence_name, last_value


def reinicia_sequence(model, ultima_pk_legado):
    ultimo_id = max(
        ultima_pk_legado,
        model.objects.latest("id").id if model.objects.exists() else 0,
    )
    sequence_name, last_value = get_sequence_name_and_last_value(model)
    if ultimo_id > last_value:
        exec_sql(
            f"""
            ALTER SEQUENCE {sequence_name}
            RESTART WITH {ultimo_id + 1} MINVALUE -1;"""
        )


REPO = git.Repo.init(DIR_REPO)  # type: ignore


def populate_renamed_fields(new, old):
    renames = field_renames[type(new)]

    for field in new._meta.fields:
        old_field_name = renames.get(field.name)
        if old_field_name:
            field_type = field.get_internal_type()

            if field_type == "ForeignKey":
                fk_field_name = "{}_id".format(field.name)
                value = get_fk_related(field, old)
                setattr(new, fk_field_name, value)
            else:
                value = getattr(old, old_field_name)

                if field_type in ("CharField", "TextField"):
                    if value in (None, "None"):
                        value = ""
                    elif isinstance(value, str):
                        # retira caracters nulos que o postgres não aceita
                        # quando usamos bulk_create
                        value = value.replace("\0", "")

                # ajusta tempos segundo timezone
                #  os campos TIMESTAMP do mysql são gravados em UTC
                #  os DATETIME e TIME não têm timezone

                if field_type == "DateTimeField" and value:
                    # as datas armazenadas no legado na verdade são naive
                    sem_tz = value.replace(tzinfo=None)  # type: ignore
                    value = PYTZ_TIMEZONE.localize(sem_tz).astimezone(pytz.utc)

                if field_type == "TimeField" and value:
                    value = value.replace(tzinfo=PYTZ_TIMEZONE)  # type: ignore

                setattr(new, field.name, value)


def roda_comando_shell(cmd):
    res = os.system(cmd)
    assert res == 0, "O comando falhou: {}".format(cmd)


def get_arquivos_ajustes_pre_migracao():
    return [
        DIR_DADOS_MIGRACAO.child("ajustes_pre_migracao", f"{SIGLA_CASA}.{sufixo}")
        for sufixo in ("sql", "reverter.yaml")
    ]


def do_flush():
    # from django.core.management.commands.flush import Command as FlushCommand
    #
    # excluindo database antigo.
    # info("Excluindo entradas antigas do banco destino.")
    # FlushCommand().handle(
    #     database="default", interactive=False, verbosity=0, allow_cascade=True
    # )
    #
    # O flush está ativando o evento em sapl.rules.apps
    # que está criando permissoes duplicadas
    # models.signals.post_migrate.connect(receiver=create_proxy_permissions, ...)
    #
    # solução => não fazer mais flush, mas verificar que o banco acabou de ser criado (está vazio)!!!!!!
    #
    # Se não estiver, recrie o banco antes para rodar a migração usando:
    # sapl/legacy/scripts/recria_um_db_postgres.sh

    for model in (
        Parlamentar,
        MateriaLegislativa,
        DocumentoAdministrativo,
        Proposicao,
        NormaJuridica,
        Protocolo,
        Mandato,
    ):
        assert not model.objects.exists()

    info("O banco acabou de ser criado e está vazio => prosseguimos")

    # apaga tipos de autor padrão (criados no flush acima)
    TipoAutor.objects.all().delete()
    # tb apagamos os dados do reversion, p nao confundir apagados_pelo_usuario
    Revision.objects.all().delete()
    Version.objects.all().delete()

    fill_vinculo_norma_juridica()


def migrar_dados(primeira_migracao=False, apagar_do_legado=False):
    try:
        # limpa tudo antes de migrar
        _cached_get_all_ids_from_model.cache_clear()
        get_pk_legado.cache_clear()
        ocorrencias.clear()
        ocorrencias.default_factory = list

        # restaura dump
        arq_dump = Path(
            DIR_DADOS_MIGRACAO.child("dumps_mysql", "{}.sql".format(NOME_BANCO_LEGADO))
        )
        assert arq_dump.exists(), "Dump do mysql faltando: {}".format(arq_dump)
        info("Restaurando dump mysql de [{}]".format(arq_dump))
        normaliza_dump_mysql(arq_dump)
        roda_comando_shell("mysql -uroot < {}".format(arq_dump))

        # desliga checagens do mysql
        # e possibilita inserir valor zero em campos de autoincremento
        exec_legado('SET SESSION sql_mode = "NO_AUTO_VALUE_ON_ZERO";')

        # executa ajustes pré-migração, se existirem
        arq_ajustes_sql, arq_ajustes_reverter = get_arquivos_ajustes_pre_migracao()
        if arq_ajustes_sql.exists():
            exec_legado(arq_ajustes_sql.read_file())
        if arq_ajustes_reverter.exists():
            revert_delete_producao(yaml.safe_load(arq_ajustes_reverter.read_file()))

        uniformiza_banco(primeira_migracao)

        if primeira_migracao:
            do_flush()
            criar_configuracao_inicial()

        info("Começando migração: ...")
        migrar_todos_os_models(apagar_do_legado)
    except Exception as e:
        ocorrencias["traceback"] = str(traceback.format_exc())  # type: ignore
        raise e
    finally:
        # congela e grava ocorrências
        ocorrencias.default_factory = None
        arq_ocorrencias = Path(REPO.working_dir, "ocorrencias.yaml")
        with open(arq_ocorrencias, "w") as arq:
            pyaml.dump(ocorrencias, arq, vspacing=1, width=200)
        REPO.git.add([arq_ocorrencias.name])
        info("Ocorrências salvas em\n  {}".format(arq_ocorrencias))
        if not ocorrencias:
            info("NÃO HOUVE OCORRÊNCIAS !!!")

    # recria tipos de autor padrão que não foram criados pela migração
    cria_models_tipo_autor()
    return ocorrencias.get("fk", [])


def move_para_depois_de(lista, movido, referencias):
    indice_inicial = lista.index(movido)
    lista.remove(movido)
    indice_apos_refs = max(lista.index(r) for r in referencias) + 1
    lista.insert(max(indice_inicial, indice_apos_refs), movido)
    return lista


def existe_reuniao_no_legado():
    return existe_tabela_no_legado("reuniao_comissao")


def get_models_a_migrar():
    models = [
        model
        for app in appconfs
        for model in app.models.values()
        if model in field_renames
    ]
    # retira reuniões quando não existe na base legada
    # (só existe no sapl 3.0)
    if not existe_reuniao_no_legado():
        models.remove(Reuniao)
    # Devido à referência TipoProposicao.tipo_conteudo_related
    # a migração de TipoProposicao precisa ser feita
    # após TipoMateriaLegislativa e TipoDocumento
    # (porém antes de Proposicao)
    move_para_depois_de(models, TipoProposicao, [TipoMateriaLegislativa, TipoDocumento])
    assert models.index(TipoProposicao) < models.index(Proposicao)
    move_para_depois_de(models, Proposicao, [MateriaLegislativa, DocumentoAcessorio])

    return models


def migrar_todos_os_models(apagar_do_legado):
    for model in get_models_a_migrar():
        migrar_model(model, apagar_do_legado)


def migrar_model(model, apagar_do_legado):
    print("Migrando %s..." % model.__name__)

    model_legado, tabela_legado, campos_pk_legado = get_estrutura_legado(model)

    if len(campos_pk_legado) == 1:

        # A PK NO LEGADO TEM UM ÚNICO CAMPO

        nome_pk = model_legado._meta.pk.name  # type: ignore
        if "ind_excluido" in {f.name for f in model_legado._meta.fields}:
            # se o model legado tem o campo ind_excluido
            # enumera apenas os não excluídos
            old_records = model_legado.objects.filter(~Q(ind_excluido=1))
        else:
            old_records = model_legado.objects.all()
        old_records = old_records.order_by(nome_pk)

        def get_id_do_legado(old):
            return getattr(old, nome_pk)

        ids_ja_migrados = get_all_ids_from_model(model)

        apagados_pelo_usuario = [
            int(v.object_id) for v in Version.objects.get_deleted(model)
        ]

        def ja_esta_migrado(old):  # type: ignore
            id = get_id_do_legado(old)
            return id in ids_ja_migrados or id in apagados_pelo_usuario

        ultima_pk_legado = (
            model_legado.objects.all().aggregate(Max("pk"))["pk__max"] or 0
        )
    else:

        # A PK NO LEGADO TEM MAIS DE UM CAMPO

        old_records = iter_sql_records(tabela_legado)
        get_id_do_legado = None  # type: ignore

        # ----------------------------------------------------------------------
        # HACK:
        #
        # Após a refatoração que introduziu parlamentares.models.MesaDiretora
        # este código parou de funcionar.
        #
        # Ele não é necessário em uma migração de primeira primeira vez.
        #
        # Certamente não acontecerá mais nenhuma migração incremental,
        # logo podemos desativá-lo
        # ----------------------------------------------------------------------
        #
        # from sapl.legacy.models import Numeracao
        # if model_legado == Numeracao:
        #     # nao usamos cod_numeracao no 3.1 => apelamos p todos os campos
        #     campos_chave = [
        #         "cod_materia",
        #         "tip_materia",
        #         "num_materia",
        #         "ano_materia",
        #         "dat_materia",
        #     ]
        # else:
        #     campos_chave = campos_pk_legado
        #
        # renames = field_renames[model]
        # campos_velhos_p_novos = {v: k for k, v in renames.items()}
        #
        # apagados_pelo_usuario = Version.objects.get_deleted(model)
        # apagados_pelo_usuario = [
        #     {k: v for k, v in get_campos_crus_reversion(version).items()}
        #     for version in apagados_pelo_usuario
        # ]
        # campos_chave_novos = {campos_velhos_p_novos[c] for c in campos_chave}
        # apagados_pelo_usuario = [
        #     {k: v for k, v in apagado.items() if k in campos_chave_novos}
        #     for apagado in apagados_pelo_usuario
        # ]
        #
        # def ja_esta_migrado(old):
        #     chave = {campos_velhos_p_novos[c]: getattr(old, c) for c in campos_chave}
        #     return (
        #         chave in apagados_pelo_usuario or model.objects.filter(**chave).exists()
        #     )
        def ja_esta_migrado(old):
            return False

        ultima_pk_legado = model_legado.objects.count()

    ajuste_antes_salvar = AJUSTE_ANTES_SALVAR.get(model)
    ajuste_depois_salvar = AJUSTE_DEPOIS_SALVAR.get(model)

    # convert old records to new ones
    with transaction.atomic():
        novos = []
        sql_delete_legado = ""
        for old in old_records:
            if ja_esta_migrado(old):
                # pulamos esse objeto, pois já foi migrado anteriormente
                continue
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
                warn("fk", e.msg, e.dados)
                continue
            else:
                new.clean()  # valida model
                novos.append(new)  # guarda para salvar

                # acumula deleção do registro no legado
                if apagar_do_legado:
                    sql_delete_legado += "delete from {} where {};\n".format(
                        tabela_legado,
                        " and ".join(
                            '{} = "{}"'.format(campo, getattr(old, campo))
                            for campo in campos_pk_legado
                        ),
                    )

        # salva novos registros
        with reversion.create_revision():
            model.objects.bulk_create(novos)
            reversion.set_comment("Objetos criados pela migração")

        if ajuste_depois_salvar:
            ajuste_depois_salvar()

        # reiniciamos a sequence logo após a última pk do legado
        #
        # É importante que seja do legado (e não da nova base),
        # pois numa nova versão da migração podemos inserir registros
        # não migrados antes sem conflito com pks criadas até lá
        if get_id_do_legado:
            reinicia_sequence(model, ultima_pk_legado)

        # apaga registros migrados do legado
        if apagar_do_legado and sql_delete_legado:
            exec_legado(sql_delete_legado)


def get_campos_crus_reversion(version):
    """Pega campos crus de uma versao do django reversion
    p evitar erros de deserialização"""
    assert version.format == "json"
    [meta] = json.loads(version.serialized_data)
    campos = meta["fields"]
    campos["id"] = meta["pk"]
    return campos


def encontra_conflitos_tipo_autor():
    # Encontrei conflito de ids em TipoAutor entre
    # um registro que existiu na base e foi apagado e um registro ressuscitado.
    # Então testamos p garantir que não associamos um ressuscitado erroneamente

    from sapl.legacy.models import TipoAutor as TipoAutorLegado

    atual = {t.id: t.descricao for t in TipoAutor.objects.all()}
    historia = {
        t.field_dict["id"]: t.field_dict["descricao"]
        for t in Version.objects.get_deleted(TipoAutor)
    }
    assert not set(atual) & set(historia)
    legado = {
        t.pk: t.des_tipo_autor
        for t in TipoAutorLegado.objects.filter(ind_excluido=False)
    }
    atual_e_historia = {**atual, **historia}
    so_no_legado = set(legado.items()) - set(atual_e_historia.items())

    # o que:
    # 1) está so no legado
    # 2) tem um id igual ao de um registro da base atual (incluindo histórico)
    # 3) mas com uma descrição difente
    conflitos = {
        id: (
            descricao_no_legado,
            atual_e_historia[id],
            "atual" if id in atual else "historia",
        )
        for id, descricao_no_legado in so_no_legado
        if id in atual_e_historia
    }
    max_id = max(*atual_e_historia, *legado)
    return conflitos, max_id


# MIGRATION_ADJUSTMENTS #####################################################


def adjust_acompanhamentomateria(
    new: AcompanhamentoMateria, old: legacy_models.AcompMateria
):
    new.confirmado = True


def adjust_documentoadministrativo(
    new: DocumentoAdministrativo, old: legacy_models.DocumentoAdministrativo
):
    if old.num_protocolo:
        numero, ano = old.num_protocolo, new.ano
        # False < True => o primeiro será o protocolo não anulado
        protocolos = Protocolo.objects.filter(numero=numero, ano=ano).order_by(
            "anulado"
        )
        if protocolos:
            new.protocolo = protocolos[0]
        else:
            # Se não achamos o protocolo registramos no número externo
            new.numero_externo = numero

            nota = """
## NOTA DE MIGRAÇÃO DE DADOS DO SAPL 2.5 ##
O número de protocolo original deste documento era [{numero}], ano [{ano}].

Não existe no sistema nenhum protocolo com estes dados
e portanto nenhum protocolo foi vinculado a este documento.

Colocamos então o número de protocolo no campo "número externo".
"""
            nota = nota.strip().format(numero=numero, ano=ano)
            msg = (
                "Protocolo {numero} faltando (referenciado "
                "no documento administrativo {cod_documento})"
            )
            warn(
                "protocolo_faltando",
                msg,
                {"numero": numero, "cod_documento": old.cod_documento, "nota": nota},
            )
            new.observacao += ("\n\n" if new.observacao else "") + nota


def adjust_mandato(new: Mandato, old: legacy_models.Mandato):
    if old.dat_fim_mandato:
        new.data_fim_mandato = old.dat_fim_mandato
    if not new.data_fim_mandato:
        legislatura = Legislatura.objects.latest("data_fim")
        new.data_fim_mandato = legislatura.data_fim
        new.data_expedicao_diploma = legislatura.data_inicio
    if not new.data_inicio_mandato:
        new.data_inicio_mandato = new.legislatura.data_inicio
        new.data_fim_mandato = new.legislatura.data_fim


def adjust_ordemdia_antes_salvar(new: OrdemDia, old: legacy_models.OrdemDia):
    new.votacao_aberta = False

    if not old.tip_votacao:
        new.tipo_votacao = 1

    if old.num_ordem is None:
        new.numero_ordem = 999999999
        warn(
            "ordem_dia_num_ordem_nulo",
            "OrdemDia de PK {pk} tinha numero ordem nulo. "
            "O valor %s foi colocado no lugar." % new.numero_ordem,
            {"pk": old.pk},
        )


def adjust_parlamentar(new: Parlamentar, old: legacy_models.Parlamentar):
    if old.ind_unid_deliberativa:
        value = new.unidade_deliberativa
        # Field is defined as not null in legacy db,
        # but data includes null values
        #  => transform None to False
        if value is None:
            warn(
                "unidade_deliberativa_nulo_p_false",
                "nulo convertido para falso na unidade_deliberativa "
                "do parlamentar {pk_parlamentar}",
                {"pk_parlamentar": old.cod_parlamentar},
            )
            new.unidade_deliberativa = False
    # migra município de residência
    if old.cod_localidade_resid:
        municipio_uf = list(
            exec_legado(
                """
            select nom_localidade, sgl_uf from localidade
            where cod_localidade = {}""".format(
                    old.cod_localidade_resid
                )
            )
        )
        if municipio_uf:
            new.municipio_residencia, new.uf_residencia = municipio_uf[0]


def adjust_participacao(new: Participacao, old: legacy_models.ComposicaoComissao):
    comissao_id, periodo_id = [
        get_fk_related(Composicao._meta.get_field(name), old)
        for name in ("comissao", "periodo")
    ]
    with reversion.create_revision():
        composicao, _ = Composicao.objects.get_or_create(
            comissao_id=comissao_id, periodo_id=periodo_id
        )
        reversion.set_comment("Objeto criado pela migração")
    new.composicao = composicao


def adjust_normarelacionada(
    new: NormaRelacionada, old: legacy_models.VinculoNormaJuridica
):
    new.tipo_vinculo = TipoVinculoNormaJuridica.objects.get(sigla=old.tip_vinculo)


def adjust_protocolo_antes_salvar(new: Protocolo, old: legacy_models.Protocolo):
    if new.numero is None:
        new.numero = old.cod_protocolo
        warn(
            "num_protocolo_nulo",
            "Número do protocolo de PK {cod_protocolo} era nulo "
            "e foi alterado para sua pk ({cod_protocolo})",
            {"cod_protocolo": old.cod_protocolo},
        )


def get_arquivo_resolve_registro_votacao():
    return DIR_DADOS_MIGRACAO.child(
        "ajustes_pre_migracao",
        "{}_resolve_registro_votacao_ambiguo.yaml".format(SIGLA_CASA),
    )


def get_como_resolver_registro_votacao_ambiguo():
    path = get_arquivo_resolve_registro_votacao()
    if path.exists():
        return yaml.safe_load(path.read_file())
    else:
        return {}


def adjust_registrovotacao_antes_salvar(
    new: RegistroVotacao, old: legacy_models.RegistroVotacao
):
    ordem_dia = OrdemDia.objects.filter(pk=old.cod_ordem, materia=old.cod_materia)
    expediente_materia = ExpedienteMateria.objects.filter(
        pk=old.cod_ordem, materia=old.cod_materia
    )

    if ordem_dia and not expediente_materia:
        new.ordem = ordem_dia[0]
    if not ordem_dia and expediente_materia:
        new.expediente = expediente_materia[0]
    # registro de votação ambíguo
    if ordem_dia and expediente_materia:
        como_resolver = get_como_resolver_registro_votacao_ambiguo()
        campo = como_resolver[new.pk]
        if campo.startswith("ordem"):
            new.ordem = ordem_dia[0]
        elif campo.startswith("expediente"):
            new.expediente = expediente_materia[0]
        else:
            raise Exception(
                """
                Registro de Votação ambíguo: {}
                Resolva criando o arquivo {}""".format(
                    new.pk, get_arquivo_resolve_registro_votacao()
                )
            )


def adjust_tipoafastamento(new: TipoAfastamento, old: legacy_models.TipoAfastamento):
    assert xor(old.ind_afastamento, old.ind_fim_mandato)
    if old.ind_afastamento:
        new.indicador = "A"
    elif old.ind_fim_mandato:
        new.indicador = "F"


def set_generic_fk(new, campo_virtual, old):
    model = campo_virtual.related_model
    new.content_type = ContentType.objects.get(
        app_label=model._meta.app_label, model=model._meta.model_name
    )
    new.object_id = get_fk_related(campo_virtual, old)


def adjust_tipoproposicao(new: TipoProposicao, old: legacy_models.TipoProposicao):
    "Aponta para o tipo relacionado de matéria ou documento"
    if old.tip_mat_ou_doc is not None:
        campo_virtual = CAMPOS_VIRTUAIS_TIPO_PROPOSICAO[old.ind_mat_ou_doc]
        set_generic_fk(new, campo_virtual, old)


def adjust_proposicao_antes_salvar(new: Proposicao, old: legacy_models.Proposicao):
    if new.data_envio:
        new.ano = new.data_envio.year
    if old.cod_mat_ou_doc is not None:
        tipo_mat_ou_doc = type(new.tipo.tipo_conteudo_related)
        campo_virtual = CAMPOS_VIRTUAIS_PROPOSICAO[tipo_mat_ou_doc]
        set_generic_fk(new, campo_virtual, old)


def adjust_statustramitacao(new: StatusTramitacao, old: legacy_models.StatusTramitacao):
    if old.ind_fim_tramitacao:
        new.indicador = "F"
    elif old.ind_retorno_tramitacao:
        new.indicador = "R"
    else:
        new.indicador = ""


def adjust_statustramitacaoadm(
    new: StatusTramitacaoAdministrativo,
    old: legacy_models.StatusTramitacaoAdministrativo,
):
    # tipagem: StatusTramitacaoAdministrativo é uma cópia de StatusTramitacao
    adjust_statustramitacao(new, old)  # type: ignore


def adjust_tramitacao(new: Tramitacao, old: legacy_models.Tramitacao):
    if old.sgl_turno == "Ú":
        new.turno = "U"


def adjust_tipo_autor(new: TipoAutor, old: legacy_models.TipoAutor):
    model_apontado = normalize(new.descricao.lower()).replace(" ", "")
    content_types = ContentType.objects.filter(model=model_apontado).exclude(
        app_label="legacy"
    )
    assert len(content_types) <= 1
    new.content_type = content_types[0] if content_types else None


def adjust_normajuridica_antes_salvar(
    new: NormaJuridica, old: legacy_models.NormaJuridica
):
    # Ajusta choice de esfera_federacao
    # O 'S' vem de 'Selecionar'. Na versão antiga do SAPL, quando uma opção do
    # combobox era selecionada, o sistema pegava a primeira letra da seleção,
    # sendo F para Federal, E para Estadual, M para Municipal e o S para
    # Selecionar, que era a primeira opção quando nada era selecionado.
    if old.tip_esfera_federacao == "S":
        new.esfera_federacao = ""


def adjust_normajuridica_depois_salvar():
    # Ajusta relação M2M
    ligacao = NormaJuridica.assuntos.through

    assuntos_migrados, normas_migradas = [
        set(model.objects.values_list("id", flat=True))
        for model in [AssuntoNorma, NormaJuridica]
    ]

    def filtra_assuntos_migrados(cod_assunto):
        """cod_assunto é uma string com cods separados por vírgulas
        p. ex.: 1,2,3,99
        """
        if not cod_assunto:
            return []
        cods = {int(a) for a in cod_assunto.split(",") if a}
        return sorted(cods.intersection(assuntos_migrados))

    old_normajurica_cod_assuntos = OldNormaJuridica.objects.filter(
        pk__in=normas_migradas
    ).values_list("pk", "cod_assunto")
    ja_migrados = set(
        ligacao.objects.values_list("normajuridica_id", "assuntonorma_id")
    )

    normas_assuntos = [
        (norma, assunto)
        for norma, cod_assunto in old_normajurica_cod_assuntos
        for assunto in filtra_assuntos_migrados(cod_assunto)
        if (norma, assunto) not in ja_migrados
    ]

    ligacao.objects.bulk_create(
        ligacao(normajuridica_id=norma, assuntonorma_id=assunto)
        for norma, assunto in normas_assuntos
    )


def adjust_autor(new: Autor, old: legacy_models.Autor):
    # vincula autor com o objeto relacionado, tentando os três campos antigos
    # o primeiro campo preenchido será usado, podendo lançar ForeignKeyFaltando
    for model_relacionado, campo_nome in [
        (Parlamentar, "nome_parlamentar"),
        (Comissao, "nome"),
        (Partido, "nome"),
    ]:
        field = CAMPOS_VIRTUAIS_AUTOR[model_relacionado]
        fk_encontrada = get_fk_related(field, old)
        if fk_encontrada:
            new.autor_related = model_relacionado.objects.get(id=fk_encontrada)
            new.nome = getattr(new.autor_related, campo_nome)
            break

    if old.col_username:
        user, created = get_user_model().objects.get_or_create(
            username=old.col_username
        )
        if created:
            # gera uma senha inutilizável, que precisará ser trocada
            user.set_password(None)
            with reversion.create_revision():
                user.save()
                reversion.set_comment(
                    "Usuário criado pela migração para o autor {}".format(old.cod_autor)
                )
        grupo_autor = Group.objects.get(name="Autor")
        user.groups.add(grupo_autor)
        # baseado em sapl/base/migrations/0046_auto_20210314_1532.py
        new.operadores.add(user)


def adjust_comissao(new: Comissao, old: legacy_models.Comissao):
    if not old.dat_extincao and not old.dat_fim_comissao:
        new.ativa = True
    elif (
        old.dat_extincao
        and date.today() < new.data_extincao
        or old.dat_fim_comissao
        and date.today() < new.data_fim_comissao
    ):
        new.ativa = True
    else:
        new.ativa = False


def adjust_tiporesultadovotacao(
    new: TipoResultadoVotacao, old: legacy_models.TipoResultadoVotacao
):
    if "aprova" in new.nome.lower():
        new.natureza = TipoResultadoVotacao.NATUREZA_CHOICES.aprovado
    elif "rejeita" in new.nome.lower():
        new.natureza = TipoResultadoVotacao.NATUREZA_CHOICES.rejeitado
    elif "retirado" in new.nome.lower():
        new.natureza = TipoResultadoVotacao.NATUREZA_CHOICES.rejeitado
    else:
        if new.nome != "DESCONHECIDO":
            # ignoramos a natureza de item criado pela migração
            warn(
                "natureza_desconhecida_tipo_resultadovotacao",
                "Não foi possível identificar a natureza do "
                'tipo de resultado de votação [{pk}: "{nome}"]',
                {"pk": new.pk, "nome": new.nome},
            )


def str_to_time(fonte):
    if not fonte.strip():
        return None
    tempo = datetime.datetime.strptime(fonte, "%H:%M")
    return tempo.time() if tempo else None


def adjust_reuniao_comissao(new: Reuniao, old: legacy_models.ReuniaoComissao):
    new.hora_inicio = str_to_time(old.hr_inicio_reuniao)


def get_mesa_diretora(cod_sessao_leg):
    sessao_legislativa = SessaoLegislativa.objects.get(pk=cod_sessao_leg)
    try:
        mesa = MesaDiretora.objects.get(sessao_legislativa=sessao_legislativa)
    except MesaDiretora.DoesNotExist:
        with reversion.create_revision():
            # cria uma mesa diretora vazia única para a sessão legislativa
            # baseado em sapl/parlamentares/migrations/0037_atribuiMesaDiretora.py
            mesa = MesaDiretora.objects.create(
                data_inicio=sessao_legislativa.data_inicio,
                data_fim=sessao_legislativa.data_fim,
                sessao_legislativa=sessao_legislativa,
            )
            reversion.set_comment("Mesa criada pela migração")
    return mesa


def adjust_composicao_mesa(new: ComposicaoMesa, old: legacy_models.ComposicaoMesa):
    new.mesa_diretora = get_mesa_diretora(old.cod_sessao_leg)


def remove_style(conteudo):
    if "style" not in conteudo:
        return conteudo  # atalho que acelera muito os casos sem style

    soup = BeautifulSoup(conteudo, "html.parser")
    for tag in soup.recursiveChildGenerator():
        if hasattr(tag, "attrs"):
            tag.attrs = {k: v for k, v in tag.attrs.items() if k != "style"}  # type: ignore
    return str(soup)


def adjust_expediente_sessao(
    new: ExpedienteSessao, old: legacy_models.ExpedienteSessaoPlenaria
):
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
    Reuniao: adjust_reuniao_comissao,
    ComposicaoMesa: adjust_composicao_mesa,
}

AJUSTE_DEPOIS_SALVAR = {NormaJuridica: adjust_normajuridica_depois_salvar}


# MARCO ######################################################################

TIME_FORMAT = "%H:%M:%S"


# permite a gravação de tempos puros pelo pretty-yaml
def time_representer(dumper, data):
    return dumper.represent_scalar("!time", data.strftime(TIME_FORMAT))


UnsafePrettyYAMLDumper.add_representer(datetime.time, time_representer)


# permite a leitura de tempos puros pelo pyyaml (no padrão gravado acima)
def time_constructor(loader, node):
    value = loader.construct_scalar(node)
    return datetime.datetime.strptime(value, TIME_FORMAT).time()


yaml.add_constructor("!time", time_constructor)

TAG_MARCO = "marco"


def gravar_marco(
    nome_dir="dados", pula_se_ja_existe=False, versiona=True, gera_backup=True
):
    """Grava um dump de todos os dados como arquivos yaml no repo de marco"""
    # prepara ou localiza repositorio
    dir_dados = Path(REPO.working_dir, nome_dir)
    if pula_se_ja_existe and dir_dados.exists():
        return
    # limpa todo o conteúdo antes
    dir_dados.rmtree()
    dir_dados.mkdir()

    # exporta dados como arquivos yaml
    user_model = get_user_model()
    models = get_models_a_migrar() + [
        Composicao,
        user_model,
        Group,
        ContentType,
    ]
    sequences = []
    for model in models:
        info(f"Gravando marco de [{model.__name__}]")
        dir_model = dir_dados.child(model._meta.app_label, model.__name__)
        dir_model.mkdir(parents=True)
        for data in model.objects.all().values():
            nome_arq = Path(dir_model, f"{data['id']}.yaml")
            with open(nome_arq, "w") as arq:
                pyaml.dump(data, arq)
        sequences.append(get_sequence_name_and_last_value(model))
    # grava valores das seqeunces
    sequences = dict(sorted(sequences))
    Path(dir_dados, "sequences.yaml").write_file(pyaml.dump(sequences))

    # backup do banco
    if gera_backup:
        print("Gerando backup do banco... ", end="", flush=True)
        arq_backup = DIR_REPO.child("{}.backup".format(NOME_BANCO_LEGADO))
        arq_backup.remove()
        backup_cmd = f"""
            pg_dump --host localhost --port 5432 --username postgres
            --no-password --format custom --blobs --verbose --file
            {arq_backup} {NOME_BANCO_LEGADO}"""
        subprocess.check_output(backup_cmd.split(), stderr=subprocess.DEVNULL)
        print("SUCESSO")

    # versiona mudanças
    if versiona:
        REPO.git.add([dir_dados.name])
        if gera_backup:
            REPO.git.add([arq_backup.name])  # type: ignore
        if "master" not in REPO.heads or REPO.index.diff("HEAD"):
            # se de fato existe mudança
            REPO.index.commit(f"Grava marco (em {nome_dir})")
        REPO.git.execute("git tag -f".split() + [TAG_MARCO])


def encode_version(version):
    # version.id seria suficiente
    # os campos reduntandes servem como conferência tanto visual
    # como de consistencia da restauracao posterior
    return {
        "id": version.id,
        "content_type__model": version.content_type.model,
        "object_id": version.object_id,
    }


def get_apagados_que_geram_ocorrencias_fk(fks_faltando):
    def get_tabela_legado_do_model(model):
        _, tabela_legado, _ = get_estrutura_legado(model)
        return tabela_legado

    tabela_legado_p_model = {
        get_tabela_legado_do_model(model): model for model in get_models_a_migrar()
    }

    apagados = set()
    for fk in fks_faltando:
        model_dependente = tabela_legado_p_model[fk["tabela"]]
        # não funciona para models em que o mapeamento de campos nao é direto
        if model_dependente in (Participacao, Autor):
            model_relacionado = {
                "cod_comissao": Comissao,
                "cod_parlamentar": Parlamentar,
            }[fk["campo"]]
        elif model_dependente == TipoProposicao:
            ind_mat_ou_doc = list(exec_legado(fk["sql"]))[0][2]
            model_relacionado = CAMPOS_VIRTUAIS_TIPO_PROPOSICAO[
                ind_mat_ou_doc
            ].related_model
        else:
            nome_campo_fk = {v: k for k, v in field_renames[model_dependente].items()}[
                fk["campo"]
            ]
            campo_fk = model_dependente._meta.get_field(nome_campo_fk)
            model_relacionado = campo_fk.related_model

        _, tabela_relacionada, [campo_pk] = get_estrutura_legado(model_relacionado)
        deleted = Version.objects.get_deleted(model_relacionado)
        versions = deleted.filter(object_id=fk["valor"])
        if versions:
            [version] = versions  # se há, deve ser único
            apagados.add((tabela_relacionada, campo_pk, version))
        # XXX poderíamos gerar aqui os parlementares apontados por autor
        # para listar como restaurado para o usuário
        # ... mas já está demais
        # nós restauramos no método abaixo, mesmo sem o feedback desse detalhe
    return [(*_, encode_version(version)) for *_, version in apagados]


def revert_delete_producao(dados_versions):
    if not dados_versions:
        return
    print("Revertendo registros apagados em produção...")
    for dados in dados_versions:
        print(dados)
        version = Version.objects.get(**dados)
        version.revert()
        reverted = version.object
        assert reverted
        # restauramos objetos relacinados ao autor
        # teoricamente precisaríamos fazer isso pra todas as generic relations
        if isinstance(reverted, Autor) and reverted.content_type:
            apagados_relacionados = Version.objects.get_deleted(
                reverted.content_type.model_class()
            )
            rel = apagados_relacionados.filter(object_id=reverted.object_id)
            if rel:
                [rel] = rel
                rel.revert()
                assert reverted.autor_related
                assert reverted.autor_related == rel.object

    print("... sucesso")


# UTILS


def porids(model):
    return {o.id: o for o in model.objects.all()}


def deletados(model):
    deletados = Version.objects.get_deleted(model)
    return {v.object_id: v for v in deletados}


def get_conflitos_materias_legado_e_producao():
    """
    Analisa conflitos entre materias nao migradas e em producao
    """
    res = list(
        exec_legado(
            """
        select cod_materia, tip_id_basica, num_ident_basica, ano_ident_basica
        from materia_legislativa where ind_excluido <> 1"""
        )
    )
    materias_legado = {(t, n, a): id for id, t, n, a in res}
    materias_producao = {
        (m.tipo_id, m.numero, m.ano): m.id for m in MateriaLegislativa.objects.all()
    }
    comuns = set(materias_legado) & set(materias_producao)
    comuns = {k: (materias_legado[k], materias_producao[k]) for k in comuns}
    conflitos = {
        k: (id_legado, id_producao)
        for k, (id_legado, id_producao) in comuns.items()
        if id_legado != id_producao
    }
    return conflitos
