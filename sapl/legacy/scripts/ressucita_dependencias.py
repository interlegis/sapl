from textwrap import dedent

import yaml
from unipath import Path

from sapl.legacy.migracao_dados import DIR_REPO, exec_legado


def stripsplit(ll):
    return [l.split() for l in ll.strip().splitlines()]


fks_legado = '''
  autor                         cod_parlamentar        parlamentar
  autor                         tip_autor              tipo_autor
  autoria                       cod_autor              autor
  expediente_materia            cod_materia            materia_legislativa
  ordem_dia                     cod_materia            materia_legislativa
  legislacao_citada             cod_norma              norma_juridica
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
  ordem_dia                     cod_sessao_plen        sessao_plenaria
  proposicao                    cod_materia            materia_legislativa
  proposicao                    cod_autor              autor
  tramitacao                    cod_status             status_tramitacao
  expediente_sessao_plenaria    cod_expediente         tipo_expediente
  proposicao                    tip_proposicao         tipo_proposicao
  tramitacao                    cod_unid_tram_dest     unidade_tramitacao
  tramitacao                    cod_unid_tram_local    unidade_tramitacao
'''
fks_legado = stripsplit(fks_legado)
fks_legado = {(o, c): t for (o, c, t) in fks_legado}


urls = '''
autor                  /sistema/autor
cargo_comissao         /sistema/comissao/cargo
legislatura            /sistema/parlamentar/legislatura
materia_legislativa    /materia
norma_juridica         /norma
parlamentar            /parlamentar
sessao_legislativa     /sistema/mesa-diretora/sessao-legislativa
sessao_plenaria        /sessao
status_tramitacao      /sistema/materia/status-tramitacao
tipo_autor             /sistema/autor/tipo
tipo_expediente        /sistema/sessao-plenaria/tipo-expediente
tipo_proposicao        /sistema/proposicao/tipo
tipo_resultado_votacao /sistema/sessao-plenaria/tipo-resultado-votacao
unidade_tramitacao     /sistema/materia/unidade-tramitacao
registro_votacao       ?????????
'''
urls = dict(stripsplit(urls))


def get_tabela_campo_valor_proposicao(fk):
    [(ind_mat_ou_doc, tip_mat_ou_doc)] = exec_legado('''
        select ind_mat_ou_doc, tip_mat_ou_doc
        from tipo_proposicao where tip_proposicao = {}
        '''.format(fk['pk']['tip_proposicao']))
    if ind_mat_ou_doc == 'M':
        return 'tipo_materia_legislativa', 'tip_materia', tip_mat_ou_doc
    elif ind_mat_ou_doc == 'D':
        return 'tipo_materia_legislativa', 'tip_documento', tip_mat_ou_doc
    else:
        raise(Exception('ind_mat_ou_doc inválido'))


CAMPOS_ORIGEM_PARA_ALVO = {
    'cod_unid_tram_dest': 'cod_unid_tramitacao',
    'cod_unid_tram_local': 'cod_unid_tramitacao',
}


def get_excluido(fk):
    tabela_origem = fk['tabela']

    if tabela_origem == 'tipo_proposicao':
        tabela_alvo, campo, valor = get_tabela_campo_valor_proposicao(fk)
    else:
        campo, valor = [fk[k] for k in ('campo', 'valor')]
        tabela_alvo = fks_legado[(tabela_origem, campo)]

    # troca nome de campo pelo correspondente na tabela alvo
    campo = CAMPOS_ORIGEM_PARA_ALVO.get(campo, campo)

    sql = 'select ind_excluido, t.* from {} t where {} = {}'.format(
        tabela_alvo, campo, valor)
    res = list(exec_legado(sql))
    return tabela_origem, campo, valor, tabela_alvo, res


def get_dependencias_a_ressucitar():
    ocorrencias = yaml.load(
        Path(DIR_REPO.child('ocorrencias.yaml').read_file()))
    fks_faltando = ocorrencias['fk']
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
        ''', []
     ),
]
SQLS_CRIACAO = {k: (dedent(sql.strip()), extras)
                for k, sql, extras in SQLS_CRIACAO}


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


def get_link(tabela_alvo, valor):
    return '{}/{}'.format(urls[tabela_alvo], valor)


def get_sql_desexcluir(tabela_alvo, campo, valor):
    sql = 'update {} set ind_excluido = 0 where {} = {};'.format(
        tabela_alvo, campo, valor)
    return sql, [get_link(tabela_alvo, valor)]


def get_sql_criar(tabela_alvo, campo, valor):
    if tabela_alvo == 'sessao_legislativa':
        sql = criar_sessao_legislativa(campo, valor)
    else:
        sql, extras = SQLS_CRIACAO[tabela_alvo]
        sql = sql.format(valor)
    links = [get_link(tabela_alvo, valor)]
    for tabela_extra, valor_extra in extras:
        links.insert(0, get_link(tabela_extra, valor_extra))
    return sql, links


TEMPLATE_RESSUCITADOS = '''
/* RESSUCITADOS

{}

*/

{}
'''


def get_sqls_desexcluir_criar(desexcluir, criar):
    sqls_links = [get_sql(tabela_alvo, campo, valor)
                  for conjunto, get_sql in ((desexcluir, get_sql_desexcluir),
                                            (criar, get_sql_criar))
                  for tabela_alvo, campo, valor in conjunto]
    if not sqls_links:
        return ''
    else:
        sqls, links = zip(*sqls_links)
        links = [l for ll in links for l in ll]  # flatten
        sqls, links = ['\n'.join(sorted(s)) for s in [sqls, links]]
        return TEMPLATE_RESSUCITADOS.format(links, sqls)


def print_ressucitar():
    desexcluir, criar = get_dependencias_a_ressucitar()
    print(get_sqls_desexcluir_criar(desexcluir, criar))
