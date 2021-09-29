
from sapl.comissoes import models as comissoes
from sapl.materia import models as materia
from sapl.rules import SAPL_GROUP_COMISSOES, __base__, __perms_publicas__
rules_group_comissoes = {
    'group': SAPL_GROUP_COMISSOES,
    'rules': [
        (materia.PautaReuniao, __base__, __perms_publicas__),
        (comissoes.Comissao, __base__, __perms_publicas__),
        (comissoes.Composicao, __base__, __perms_publicas__),
        (comissoes.Participacao, __base__, __perms_publicas__),
        (materia.Relatoria, __base__, __perms_publicas__),
        (comissoes.Reuniao, __base__, __perms_publicas__),
        (comissoes.DocumentoAcessorio, __base__, __perms_publicas__),
    ]
}
