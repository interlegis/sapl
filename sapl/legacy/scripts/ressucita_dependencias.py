import yaml
from unipath import Path

from sapl.legacy.migracao_dados import DIR_REPO, exec_legado

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
'''
fks_legado = [l.split() for l in fks_legado.strip().splitlines()]
fks_legado = {(o, c): t for (o, c, t) in fks_legado}


def get_excluido(fk):
    campo, valor, tabela_origem = [fk[k] for k in ('campo', 'valor', 'tabela')]
    tabela_alvo = fks_legado[(tabela_origem, campo)]
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


SQLS_CRIACAO = {
    'tipo_proposicao': '''
        insert into tipo_materia_legislativa (
        tip_materia, sgl_tipo_materia, des_tipo_materia, ind_num_automatica,
        quorum_minimo_votacao, ind_excluido)
        values (0, "DESC", "DESCONHECIDO", 0, 0, 0);

        insert into tipo_proposicao (
        tip_proposicao, des_tipo_proposicao, ind_mat_ou_doc, tip_mat_ou_doc,
        nom_modelo, ind_excluido)
        values ({}, "DESCONHECIDO", "M", 0, "DESCONHECIDO", 0);
''',
}


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


def get_sql_desexcluir(tabela_alvo, campo, valor):
    return 'update {} set ind_excluido = 0 where {} = {};'.format(
        tabela_alvo, campo, valor)


def get_sql_criar(tabela_alvo, campo, valor):
    if tabela_alvo == 'sessao_legislativa':
        return criar_sessao_legislativa(campo, valor)
    else:
        sql = SQLS_CRIACAO[tabela_alvo]
        return sql.format(valor)


TEMPLATE_RESSUCITADOS = '''
/* RESSUCITADOS * /

{}
'''


def get_sqls_desexcluir_criar(desexcluir, criar):
    sqls = [get_sql(tabela_alvo, campo, valor)
            for conjunto, get_sql in ((desexcluir, get_sql_desexcluir),
                                      (criar, get_sql_criar))
            for tabela_alvo, campo, valor in conjunto]
    if not sqls:
        return ''
    else:
        return TEMPLATE_RESSUCITADOS.format('\n'.join(sorted(sqls)))


def print_ressucitar():
    desexcluir, criar = get_dependencias_a_ressucitar()
    print(get_sqls_desexcluir_criar(desexcluir, criar))
