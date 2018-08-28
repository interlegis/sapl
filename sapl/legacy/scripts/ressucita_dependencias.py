from textwrap import dedent

import texttable
import yaml
from unipath import Path

from sapl.legacy.migracao_dados import (DIR_REPO, PROPAGACOES_DE_EXCLUSAO,
                                        exec_legado)


def stripsplit(ll):
    return [l.split() for l in ll.strip().splitlines()]


fks_legado = '''
  autor                         cod_parlamentar        parlamentar
  autor                         tip_autor              tipo_autor
  autoria                       cod_autor              autor
  oradores                      cod_parlamentar        parlamentar
  oradores_expediente           cod_parlamentar        parlamentar
  ordem_dia_presenca            cod_parlamentar        parlamentar
  protocolo                     cod_autor              autor
  registro_votacao              tip_resultado_votacao  tipo_resultado_votacao
  registro_votacao_parlamentar  cod_parlamentar        parlamentar
  registro_votacao_parlamentar  cod_votacao            registro_votacao
  sessao_legislativa            num_legislatura        legislatura
  sessao_plenaria_presenca      cod_parlamentar        parlamentar
  composicao_comissao           cod_cargo              cargo_comissao
  sessao_plenaria               cod_sessao_leg         sessao_legislativa
  proposicao                    cod_materia            materia_legislativa
  proposicao                    cod_autor              autor
  tramitacao                    cod_status             status_tramitacao
  expediente_sessao_plenaria    cod_expediente         tipo_expediente
  proposicao                    tip_proposicao         tipo_proposicao
  tramitacao                    cod_unid_tram_dest     unidade_tramitacao
  tramitacao                    cod_unid_tram_local    unidade_tramitacao
  tramitacao_administrativo     cod_unid_tram_dest     unidade_tramitacao
  tramitacao_administrativo     cod_unid_tram_local    unidade_tramitacao
  documento_acessorio           tip_documento          tipo_documento
  relatoria                     cod_parlamentar        parlamentar
  relatoria                     cod_materia            materia_legislativa
  unidade_tramitacao            cod_orgao              orgao
  norma_juridica                cod_materia            materia_legislativa
  sessao_plenaria               tip_sessao             tipo_sessao_plenaria
  mesa_sessao_plenaria          cod_cargo              cargo_mesa
  norma_juridica                tip_norma              tipo_norma_juridica
  materia_legislativa           tip_id_basica          tipo_materia_legislativa
  despacho_inicial              cod_comissao           comissao
  relatoria                     cod_comissao           comissao
'''
fks_legado = stripsplit(fks_legado)
fks_legado = {(o, c): t for (o, c, t) in fks_legado}


urls = '''
autor                    /sistema/autor
cargo_comissao           /sistema/comissao/cargo
legislatura              /sistema/parlamentar/legislatura
materia_legislativa      /materia
norma_juridica           /norma
parlamentar              /parlamentar
sessao_legislativa       /sistema/mesa-diretora/sessao-legislativa
sessao_plenaria          /sessao
status_tramitacao        /sistema/materia/status-tramitacao
tipo_autor               /sistema/autor/tipo
tipo_expediente          /sistema/sessao-plenaria/tipo-expediente
tipo_proposicao          /sistema/proposicao/tipo
tipo_resultado_votacao   /sistema/sessao-plenaria/tipo-resultado-votacao
unidade_tramitacao       /sistema/materia/unidade-tramitacao
tipo_documento           /sistema/materia/tipo-documento
orgao                    /sistema/materia/orgao
tipo_sessao_plenaria     /sistema/sessao-plenaria/tipo
cargo_mesa               /sistema/mesa-diretora/cargo-mesa
documento_administrativo /docadm
tipo_materia_legislativa /sistema/materia/tipo
tipo_norma_juridica      /sistema/norma/tipo
comissao                 /comissao
registro_votacao         ?????????
'''
urls = dict(stripsplit(urls))


def get_tabela_campo_tipo_proposicao(tip_proposicao):
    [(ind_mat_ou_doc,)] = exec_legado('''
        select ind_mat_ou_doc from tipo_proposicao where tip_proposicao = {};
        '''.format(tip_proposicao))
    if ind_mat_ou_doc == 'M':
        return 'tipo_materia_legislativa', 'tip_materia'
    elif ind_mat_ou_doc == 'D':
        return 'tipo_documento', 'tip_documento'
    else:
        raise(Exception('ind_mat_ou_doc inválido'))


CAMPOS_ORIGEM_PARA_ALVO = {
    'cod_unid_tram_dest': 'cod_unid_tramitacao',
    'cod_unid_tram_local': 'cod_unid_tramitacao',
    'tip_id_basica': 'tip_materia',
}


def get_excluido(fk):
    tabela_origem, campo, valor = [fk[k] for k in ('tabela', 'campo', 'valor')]

    if tabela_origem == 'tipo_proposicao':
        tip_proposicao = fk['pk']['tip_proposicao']
        tabela_alvo, campo = get_tabela_campo_tipo_proposicao(tip_proposicao)
    elif tabela_origem == 'proposicao' and campo == 'cod_mat_ou_doc':
        [(ind_mat_ou_doc,)] = exec_legado('''
            select ind_mat_ou_doc from
                proposicao p inner join tipo_proposicao t
                on p.tip_proposicao = t.tip_proposicao
            where cod_proposicao = {};
        '''.format(fk['pk']['cod_proposicao']))
        if ind_mat_ou_doc == 'M':
            tabela_alvo, campo = 'materia_legislativa', 'cod_materia'
        elif ind_mat_ou_doc == 'D':
            tabela_alvo, campo = 'documento_acessorio', 'cod_documento'
        else:
            raise(Exception('ind_mat_ou_doc inválido'))
    else:
        tabela_alvo = fks_legado[(tabela_origem, campo)]

    # troca nome de campo pelo correspondente na tabela alvo
    campo = CAMPOS_ORIGEM_PARA_ALVO.get(campo, campo)

    sql = 'select ind_excluido, t.* from {} t where {} = {}'.format(
        tabela_alvo, campo, valor)
    res = list(exec_legado(sql))
    return tabela_origem, campo, valor, tabela_alvo, res


def get_desc_materia(cod_materia):
    sql = '''
        select t.sgl_tipo_materia, t.des_tipo_materia,
            m.num_ident_basica, m.ano_ident_basica
        from materia_legislativa m inner join tipo_materia_legislativa t
            on m.tip_id_basica = t.tip_materia
        where cod_materia = {};
    '''.format(cod_materia)
    return list(exec_legado(sql))[0]


def get_link_proposicao(cod_proposicao, slug):
    url_base = get_url(slug)
    return 'http://{}/cadastros/proposicao/proposicao_mostrar_proc?cod_proposicao={}'.format(  # noqa
        url_base, cod_proposicao)


def get_apaga_materias_de_proposicoes(fks, slug):
    refs_materias = [['id proposicao', 'sigla tipo matéria',
                      'tipo matéria', 'número matéria', 'ano matéria']]
    sqls = []
    cods_proposicoes = []

    for fk in fks:
        cod_proposicao = fk['pk']['cod_proposicao']
        cods_proposicoes.append(cod_proposicao)
        assert fk['campo'] == 'cod_materia'
        up = 'update proposicao set cod_materia = NULL where cod_proposicao = {};'  # noqa
        refs_materias.append(
            [cod_proposicao, *get_desc_materia(fk['valor'])])
        sqls.append(up.format(cod_proposicao))

    table = texttable.Texttable()
    table.set_cols_width([10, 10, 50, 10, 10])
    table.set_deco(table.VLINES | table.HEADER)
    table.add_rows(refs_materias)

    links = '\n'.join([get_link_proposicao(p, slug)
                       for p in cods_proposicoes])
    sqls = '\n'.join(sqls)
    if not sqls:
        return ''
    else:
        return '''
/* REFERÊNCIAS A MATÉRIAS APAGADAS DE PROPOSIÇÕES

ATENÇÃO

As seguintes proposições apontaram no passado para matérias
e esses apontamentos foram em algum momento retirados.

Elas foram migradas da forma com estão agora: sem apontar para nenhuma matéria.
Entretanto, talvez você deseje rever esses apontamentos.

Segue então uma lista dos apontamentos anteriores que detectamos.

{}

Para facilitar sua conferência, seguem os links para as proposições envolvidas:

{}

*/

{}

    '''.format(table.draw(), links, sqls)


def get_dependencias_a_ressucitar(slug):
    ocorrencias = yaml.load(
        Path(DIR_REPO.child('ocorrencias.yaml').read_file()))
    fks_faltando = ocorrencias.get('fk')
    if not fks_faltando:
        return [], []

    proposicoes_para_materia = [
        fk for fk in fks_faltando
        if fk['tabela'] == 'proposicao' and fk['campo'] == 'cod_materia']

    print(get_apaga_materias_de_proposicoes(proposicoes_para_materia, slug))

    propagacoes = {(o, c) for t, o, c in PROPAGACOES_DE_EXCLUSAO}

    fks_faltando = [fk for fk in fks_faltando
                    if fk not in proposicoes_para_materia
                    and (fk['tabela'], fk['campo']) not in propagacoes]

    excluidos = [get_excluido(fk) for fk in fks_faltando]
    desexcluir, criar = [
        set([(tabela_alvo, campo, valor)
             for tabela_origem, campo, valor, tabela_alvo, res in excluidos
             if condicao(res)])
        for condicao in (
            # o registro existe e ind_excluido == 1
            lambda res: res and res[0][0] == 1,
            # o registro não existe
            lambda res: not res
        )]
    return desexcluir, criar


SQLS_CRIACAO = [
    ('tipo_proposicao', '''
        insert into tipo_materia_legislativa (
        tip_materia, sgl_tipo_materia, des_tipo_materia, ind_num_automatica,
        quorum_minimo_votacao, ind_excluido)
        values (0, "DESC", "DESCONHECIDO", 0, 0, 0);

        insert into tipo_proposicao (
        tip_proposicao, des_tipo_proposicao, ind_mat_ou_doc, tip_mat_ou_doc,
        nom_modelo, ind_excluido)
        values ({}, "DESCONHECIDO", "M", 0, "DESCONHECIDO", 0);
        ''', ['tipo_materia_legislativa', 0]
     ),
    ('tipo_resultado_votacao', '''
        insert into tipo_resultado_votacao (
        tip_resultado_votacao, nom_resultado, ind_excluido)
        values ({}, "DESCONHECIDO", 0);
        '''),
    ('tipo_autor', '''
        insert into tipo_autor (tip_autor, des_tipo_autor, ind_excluido)
        values ({}, "DESCONHECIDO", 0);
     '''),
    ('unidade_tramitacao', '''
        insert into unidade_tramitacao (cod_unid_tramitacao, cod_comissao, cod_orgao, cod_parlamentar, ind_excluido)
        values ({}, NULL, NULL, NULL, 0);
     '''),
]
SQLS_CRIACAO = {k: (dedent(sql.strip()), extras)
                for k, sql, *extras in SQLS_CRIACAO}


def criar_sessao_legislativa(campo, valor):
    assert campo == 'cod_sessao_leg'
    [(num_legislatura,)] = exec_legado(
        'select min(num_legislatura) from legislatura where ind_excluido <> 1')
    return '''
insert into sessao_legislativa (
    cod_sessao_leg, num_legislatura, num_sessao_leg, tip_sessao_leg,
    dat_inicio, dat_fim, dat_inicio_intervalo, dat_fim_intervalo,
ind_excluido) values ({}, {}, 0, "O",
    "1900-01-01", "1900-01-02", "1900-01-01", "1900-01-02", 0);
        '''.format(valor, num_legislatura)


def get_link(tabela_alvo, valor, slug):
    url_base = get_url(slug)
    return 'http://{}{}/{}'.format(url_base, urls[tabela_alvo], valor)


def get_sql_desexcluir(tabela_alvo, campo, valor, slug):
    sql = 'update {} set ind_excluido = 0 where {} = {};'.format(
        tabela_alvo, campo, valor)
    return sql, [get_link(tabela_alvo, valor, slug)]


def get_sql_criar(tabela_alvo, campo, valor, slug):
    if tabela_alvo == 'sessao_legislativa':
        sql = criar_sessao_legislativa(campo, valor)
    else:
        sql, extras = SQLS_CRIACAO[tabela_alvo]
        sql = sql.format(valor)
    links = [get_link(tabela_alvo, valor, slug)]
    for tabela_extra, valor_extra in extras:
        links.insert(0, get_link(tabela_extra, valor_extra, slug))
    return sql, links


TEMPLATE_RESSUCITADOS = '''
/* RESSUCITADOS


SOBRE REGISTROS QUE ESTAVAM APAGADOS E FORAM RESTAURADOS

Os registros que listamos a seguir estavam excluídos (ou simplesmente não existiam) no sistema antigo e precisaram ser restaurados (ou criados) para completarmos a migração. Foi necessário fazer isso pois outros registros ativos no sistema apontam para eles.
Vocês agora podem decidir mantê-los, ajustá-los ou excluí-los. Segue a lista:

{}

Se a opção for por excluir um desses registros novamente, note que só será possível fazer isso quando nada mais no sistema fizer referência a ele.

Ao tentar excluir um registro usado em outras partes do sistema, você verá uma lista dos itens que apontam para ele de alguma forma. Para conseguir excluir você deve editar cada dos dos itens dependentes lista mostrada, retirando ou trocando a referência ao que deseja excluir.

*/

{}
'''


def get_url(slug):
    return 'sapl31.{}.leg.br'.format(slug.replace('-', '.'))


def get_sqls_desexcluir_criar(desexcluir, criar, slug):
    sqls_links = [get_sql(*(args + (slug,)))
                  for itens, get_sql in ((desexcluir, get_sql_desexcluir),
                                         (criar, get_sql_criar))
                  for args in itens]
    if not sqls_links:
        return ''
    else:
        sqls, links = zip(*sqls_links)
        links = [l for ll in links for l in ll]  # flatten
        sqls, links = ['\n'.join(sorted(s)) for s in [sqls, links]]
        return TEMPLATE_RESSUCITADOS.format(links, sqls)


def print_ressucitar(slug):
    desexcluir, criar = get_dependencias_a_ressucitar(slug)
    print(get_sqls_desexcluir_criar(desexcluir, criar, slug))
