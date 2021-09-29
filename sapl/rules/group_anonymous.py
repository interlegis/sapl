
from sapl.materia import models as materia
from sapl.protocoloadm import models as protocoloadm
from sapl.rules import SAPL_GROUP_ANONYMOUS, RP_ADD, RP_DELETE

# não possui efeito e é usada nos testes que verificam se todos os models estão
# neste arquivo rules.py
rules_group_anonymous = {
    'group': SAPL_GROUP_ANONYMOUS,
    'rules': [
        (materia.AcompanhamentoMateria, [RP_ADD, RP_DELETE], set()),
        (protocoloadm.AcompanhamentoDocumento, [RP_ADD, RP_DELETE], set()),
    ]
}
