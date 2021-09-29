from sapl.compilacao import models as compilacao
from sapl.materia import models as materia
from sapl.rules import SAPL_GROUP_AUTOR, __base__, __perms_publicas__
rules_group_autor = {
    'group': SAPL_GROUP_AUTOR,
    'rules': [
        (materia.Proposicao, __base__, set()),
        (materia.HistoricoProposicao, __base__, set()),
        (compilacao.Dispositivo, __base__ + [
            'change_your_dispositivo_edicao_dinamica',
        ], __perms_publicas__)
    ]
}
