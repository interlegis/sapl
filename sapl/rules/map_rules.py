from sapl.rules import SAPL_GROUP_LOGIN_SOCIAL
from sapl.rules.group_administrativo import rules_group_administrativo
from sapl.rules.group_anonymous import rules_group_anonymous
from sapl.rules.group_audiencia import rules_group_audiencia
from sapl.rules.group_autor import rules_group_autor
from sapl.rules.group_comissoes import rules_group_comissoes
from sapl.rules.group_geral import rules_group_geral
from sapl.rules.group_materia import rules_group_materia
from sapl.rules.group_norma import rules_group_norma
from sapl.rules.group_painel import rules_group_painel
from sapl.rules.group_protocolo import rules_group_protocolo
from sapl.rules.group_sessao import rules_group_sessao
from sapl.rules.group_votante import rules_group_votante

rules_group_login_social = {
    'group': SAPL_GROUP_LOGIN_SOCIAL,
    'rules': []
}
"""
ESTRUTURA DAS RULES DEFINIDAS NOS ARQUIVOS GROUP_[DEFINICAO].PY

todos as rules de groups são um dicionario com duas chaves: 'group' e 'rules'

'group' precisa ser um dos grupos definidos em sapl.rules.__init__.py

'rules' é uma  lista de tuplas de três posições, onde
    0 - de que model se trata
    1 - list - quais permissões possui um usuário ligado ao grupo para o model da posição 0
      - também indica ao CRUD que sua subclasse ligada a um radical precisa exigir credencial
    2 - set - indica a API quais permissões são públicas, ou seja,
        se está no set é um o acesso ao endpoint é público

exemplo:

rules_group_exemplo = {
    'group': SAPL_GROUP_EXEMPLO,
    'rules': [
        (
            model_exemplo1,
            ( RP_LIST, RP_DETAIL ),
            set()
        ),
        (
            model_exemplo2,
            (RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE),
            {RP_LIST, RP_DETAIL}
        ),
    ]
}

rules_group_exemplo['rules'][0]
  1 significa q usuários que estão no grupo SAPL_GROUP_EXEMPLO
    só podem acessar o que está em rules_group_exemplo['rules'][0][1], ou seja,
    listar e ver os detalhes de model_exemplo1

  1 significa também que o crud exigirá tais credenciais no listview e detailview

  2 set() diz que, na API, não existe acesso anônimo

--------------------------

rules_group_exemplo['rules'][1]
  1 significa q usuários que estão no grupo SAPL_GROUP_EXEMPLO
    podem acessar o que está em rules_group_exemplo['rules'][1][1], ou seja,
    listar, ver detalhes, editar, apagar e adicionar registros de model_exemplo2

  1 significa também que o crud exigirá tais credenciais em todos as suas views

  2 {RP_LIST, RP_DETAIL} diz que, na API, só list e detail pode ser acessado sem credencial.

"""

rules_group_geral['rules'] = (rules_group_geral['rules'] +
                              rules_group_administrativo['rules'] +
                              rules_group_protocolo['rules'] +
                              rules_group_comissoes['rules'] +
                              rules_group_audiencia['rules'] +
                              rules_group_materia['rules'] +
                              rules_group_norma['rules'] +
                              rules_group_sessao['rules'] +
                              rules_group_painel['rules'] +
                              rules_group_login_social['rules'])

rules_patterns = [
    rules_group_audiencia,
    rules_group_administrativo,
    rules_group_protocolo,
    rules_group_comissoes,
    rules_group_materia,
    rules_group_norma,
    rules_group_sessao,
    rules_group_painel,
    rules_group_geral,
    rules_group_autor,
    rules_group_votante,

    rules_group_anonymous,  # anotação para validação do teste de rules
    rules_group_login_social  # TODO não implementado
]

rules_patterns_public = {}


def _get_registration_key(model):
    return '%s:%s' % (model._meta.app_label, model._meta.model_name)


for rules_group in rules_patterns:
    for rs in rules_group['rules']:
        key = _get_registration_key(rs[0])
        if key not in rules_patterns_public:
            rules_patterns_public[key] = set()

        r = set(map(lambda x, m=rs[0]: '{}{}{}'.format(
            m._meta.app_label,
            x,
            m._meta.model_name), rs[2]))
        rules_patterns_public[key] = rules_patterns_public[key] | r
