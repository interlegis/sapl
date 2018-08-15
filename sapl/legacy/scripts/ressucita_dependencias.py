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
    fks = ocorrencias['fk']
    excluidos = [get_excluido(fk) for fk in fks]
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


def get_sqls_desexcluir_criar(desexcluir, criar):
    sqls_desexcluir = [
        'update {} set ind_excluido = 0 where {} = {};'.format(
            tabela_alvo, campo, valor)
        for tabela_alvo, campo, valor in desexcluir]
    return '\n'.join(sqls_desexcluir)
