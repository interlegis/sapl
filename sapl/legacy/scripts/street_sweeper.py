#!/usr/bin/python

# requisito: pip install PyMySQL

import pymysql.cursors

HOST = 'localhost'
USER = 'root'
PASSWORD = ''
DB = ''


SELECT_EXCLUIDOS = "SELECT %s FROM %s WHERE ind_excluido = 1 ORDER BY %s"

REGISTROS_INCONSISTENTES = "DELETE FROM %s WHERE %s "
"in (%s) AND ind_excluido = 0 "

EXCLUI_REGISTRO = "DELETE FROM %s WHERE ind_excluido=1"

NORMA_DEP = "DELETE FROM vinculo_norma_juridica WHERE cod_norma_referente in (%s) OR \
               cod_norma_referida in (%s) AND ind_excluido = 0 "

mapa = {}  # mapa com tabela principal -> tabelas dependentes

mapa['tipo_autor'] = ['autor']
mapa['materia_legislativa'] = ['acomp_materia', 'autoria', 'despacho_inicial',
                               'documento_acessorio', 'expediente_materia',
                               'legislacao_citada', 'materia_assunto',
                               'numeracao', 'ordem_dia', 'parecer',
                               'proposicao', 'registro_votacao',
                               'relatoria', 'tramitacao']
mapa['norma_juridica'] = ['vinculo_norma_juridica']
mapa['comissao'] = ['composicao_comissao']
mapa['sessao_legislativa'] = ['composicao_mesa']
mapa['tipo_expediente'] = ['expediente_sessao_plenaria']

"""
mapa['autor'] = ['tipo_autor', 'partido', 'comissao', 'parlamentar']
mapa['parlamentar'] = ['autor', 'autoria', 'composicao_comissao',
                       'composicao_mesa', 'dependente', 'filiacao',
                       'mandato', 'mesa_sessao_plenaria', 'oradores',
                       'oradores_expediente', 'ordem_dia_presenca',
                       'registro_votacao_parlamentar', 'relatoria',
                       'sessao_plenaria_presenca', 'unidade_tramitacao']
"""


def get_ids_excluidos(cursor, query):
    """
        recupera as PKs de registros com ind_excluido = 1 da tabela principal
    """
    cursor.execute(query)
    excluidos = cursor.fetchall()
    # flat tuple of tuples with map transformation into string
    excluidos = [str(val) for sublist in excluidos for val in sublist]
    return excluidos


def remove_tabelas(cursor, tabela_principal, pk, query_dependentes=None):

    QUERY = SELECT_EXCLUIDOS % (pk, tabela_principal, pk)
    ids_excluidos = get_ids_excluidos(cursor, QUERY)
    print("\nRegistros da tabela '%s' com ind_excluido = 1: %s" %
          (tabela_principal.upper(), len(ids_excluidos)))

    """
        Remove registros de tabelas que dependem da tabela principal,
        e que se encontram com ind_excluido = 0 (nao excluidas), se
        tais registros existirem.
    """
    if ids_excluidos:
        print("Dependencias inconsistentes")
        for tabela in mapa[tabela_principal]:

            QUERY_DEP = REGISTROS_INCONSISTENTES % (
                tabela, pk, ','.join(ids_excluidos))

            # Trata caso especifico de norma_juridica
            if query_dependentes:
                QUERY_DEP = query_dependentes % (','.join(ids_excluidos),
                                                 ','.join(ids_excluidos))

            print(tabela.upper(), cursor.execute(QUERY_DEP))

    """
        Remove todos os registros com ind_excluido = 1 das tabelas
        dependentes e da tabela principal, nesta ordem.
    """
    print("\n\nRegistros com ind_excluido = 1")
    for tabela in mapa[tabela_principal] + [tabela_principal]:
        QUERY = EXCLUI_REGISTRO % tabela
        print(tabela.upper(), cursor.execute(QUERY))


def remove_excluidas(cursor):
    cursor.execute("SHOW_TABLES")
    for row in cursor.fetchall():
        print(row)


def remove_proposicao_invalida(cursor):
    return cursor.execute(
        "DELETE FROM proposicao WHERE cod_mat_ou_doc is null")


def remove_materia_assunto_invalida(cursor):
    return cursor.execute(
        "DELETE FROM materia_assunto WHERE cod_assunto = 0")


def shotgun_remove(cursor):
    for tabela in get_ids_excluidos(cursor, "SHOW TABLES"):
        try:
            cursor.execute("DELETE FROM %s WHERE ind_excluido = 1" % tabela)
        except:
            pass


if __name__ == '__main__':
    connection = pymysql.connect(host=HOST,
                                 user=USER,
                                 password=PASSWORD,
                                 db=DB)
    cursor = connection.cursor()
    # TIPO AUTOR
    remove_tabelas(cursor, 'tipo_autor', 'tip_autor')
    # MATERIA LEGISLATIVA
    remove_tabelas(cursor, 'materia_legislativa', 'cod_materia')
    # NORMA JURIDICA
    remove_tabelas(cursor, 'norma_juridica', 'cod_norma', NORMA_DEP)
    # COMISSAO
    remove_tabelas(cursor, 'comissao', 'cod_comissao')
    # SESSAO LEGISLATIVA
    remove_tabelas(cursor, 'sessao_legislativa', 'cod_sessao_leg')
    # EXPEDIENTE SESSAO
    remove_tabelas(cursor, 'tipo_expediente', 'cod_expediente')
    # AUTOR
    remove_tabelas(cursor, 'autor', 'cod_autor')
    # PARLAMENTAR
    remove_tabelas(cursor, 'parlamentar', 'cod_parlamentar')

    # PROPOSICAO
    remove_proposicao_invalida(cursor)

    # MATERIA_ASSUNTO
    remove_materia_assunto_invalida(cursor)

    # shotgun_remove(cursor)

    cursor.close()
