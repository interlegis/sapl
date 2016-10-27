from django.utils.translation import ugettext_lazy as _

default_app_config = 'sapl.rules.apps.AppConfig'


SAPL_GROUP_ADMINISTRATIVO = _("Operador Administrativo")
SAPL_GROUP_PROTOCOLO = _("Operador de Protocolo Administrativo")
SAPL_GROUP_COMISSOES = _("Operador de Comissões")
SAPL_GROUP_MATERIA = _("Operador de Matéria")
SAPL_GROUP_NORMA = _("Operador de Norma Jurídica")
SAPL_GROUP_SESSAO = _("Operador de Sessão Plenária")
SAPL_GROUP_PAINEL = _("Operador de Painel Eletrônico")
SAPL_GROUP_GERAL = _("Operador Geral")
SAPL_GROUP_AUTOR = _("Autor")
SAPL_GROUP_PARLAMENTAR = _("Parlamentar")

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
    SAPL_GROUP_PARLAMENTAR,
    SAPL_GROUP_LOGIN_SOCIAL,
    SAPL_GROUP_ANONYMOUS,
]
