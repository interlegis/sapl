from sapl.painel import models as painel
from sapl.rules import SAPL_GROUP_PAINEL, __base__, __perms_publicas__

rules_group_painel = {
    'group': SAPL_GROUP_PAINEL,
    'rules': [
        (painel.Painel, __base__, __perms_publicas__),
        (painel.Cronometro, __base__, __perms_publicas__),
    ]
}
