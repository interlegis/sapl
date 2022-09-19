from django.utils.translation import ugettext_lazy as _

default_app_config = 'sapl.rules.apps.AppConfig'

"""
Todas as permissões do django framework seguem o padrão

        [app_label].[radical_de_permissao]_[model]

ou seja, em sapl.norma.NormaJuridica, por exemplo, o django framework cria
três permissões registadas na classe Permission:

        definição                         uso

        - add_normajuridica               norma.add_normajuridica
        - change_normajuridica            norma.change_normajuridica
        - delete_normajuridica            norma.delete_normajuridica

        - view_normajuridica              norma.view_normajuridica
        # o radical .view_ não existia no django quando a app rules foi criada
        # e portanto não é utilizada

No SAPL foram acrescidas em todos os models as duas regras abaixo, adicionadas
com o Signal post_migrate `create_proxy_permissions`
localizado em sapl.rules.apps.py.

        - list_normajuridica              norma.list_normajuridica
        - detail_normajuridica            norma.detail_normajuridica

Tanto o Crud implementado em sapl.crud.base.py quanto o Signal post_migrate
`update_groups` que é responsável por ler o mapa do
arquivo (sapl.rules.map_rules.py) e criar os grupos definidos na regra de
negócio trabalham com os cinco radiais de permissão
e com qualquer outro tipo de permissão customizada, nesta ordem de precedência.

Os cinco radicais de permissão são, portanto:

        RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE =\
            '.list_', '.detail_', '.add_', '.change_', '.delete_',

Tanto a app crud quanto a app rules estão sempre ligadas a um model. Ao lidar
com permissões, sempre é analisado se é apenas um radical ou permissão
completa, sendo apenas um radical, a permissão completa é montada com base
no model associado.

NESTE ARQUIVO ESTÃO DEFINIDOS OS RADICAIS E OS GRUPOS DEFAULT DO SAPL

"""

RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE = \
    '.list_', '.detail_', '.add_', '.change_', '.delete_',

__base__ = [RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE]
__listdetailchange__ = [RP_LIST, RP_DETAIL, RP_CHANGE]

__perms_publicas__ = {RP_LIST, RP_DETAIL}

SAPL_GROUP_ADMINISTRATIVO = _("Operador Administrativo")
SAPL_GROUP_AUDIENCIA = _("Operador de Audiência")
SAPL_GROUP_PROTOCOLO = _("Operador de Protocolo Administrativo")
SAPL_GROUP_COMISSOES = _("Operador de Comissões")
SAPL_GROUP_MATERIA = _("Operador de Matéria")
SAPL_GROUP_NORMA = _("Operador de Norma Jurídica")
SAPL_GROUP_SESSAO = _("Operador de Sessão Plenária")
SAPL_GROUP_PAINEL = _("Operador de Painel Eletrônico")
SAPL_GROUP_GERAL = _("Operador Geral")
SAPL_GROUP_AUTOR = _("Autor")
SAPL_GROUP_VOTANTE = _("Votante")

# TODO - funcionalidade ainda não existe mas está aqui para efeito de anotação
SAPL_GROUP_LOGIN_SOCIAL = _("Usuários com Login Social")

# ANONYMOUS não é um grupo mas é uma variável usadas nas rules para anotar
# explicitamente models que podem ter ação de usuários anônimos
# como por exemplo AcompanhamentoMateria
SAPL_GROUP_ANONYMOUS = ''

SAPL_GROUPS = [
    SAPL_GROUP_ADMINISTRATIVO,
    SAPL_GROUP_PROTOCOLO,
    SAPL_GROUP_COMISSOES,
    SAPL_GROUP_MATERIA,
    SAPL_GROUP_NORMA,
    SAPL_GROUP_SESSAO,
    SAPL_GROUP_PAINEL,
    SAPL_GROUP_GERAL,
    SAPL_GROUP_AUTOR,
    SAPL_GROUP_VOTANTE,
    SAPL_GROUP_LOGIN_SOCIAL,
    SAPL_GROUP_ANONYMOUS,
]

SAPL_GROUPS_DELETE = [

]
