from sapl.compilacao import models as compilacao
from sapl.materia import models as materia
from sapl.protocoloadm import models as protocoloadm
from sapl.rules import SAPL_GROUP_PROTOCOLO, RP_ADD, __base__, __listdetailchange__, \
    __perms_publicas__

rules_group_protocolo = {
    'group': SAPL_GROUP_PROTOCOLO,
    'rules': [
        (protocoloadm.Protocolo, __base__ + ['action_anular_protocolo'], set()),
        (protocoloadm.DocumentoAdministrativo, [RP_ADD] + __listdetailchange__, set()),
        (protocoloadm.DocumentoAcessorioAdministrativo, __listdetailchange__, set()),

        (materia.MateriaLegislativa, __listdetailchange__, __perms_publicas__),
        (materia.MateriaLegislativa, ['can_access_impressos'], __perms_publicas__),
        (materia.DocumentoAcessorio, __listdetailchange__, __perms_publicas__),
        (materia.Anexada, __base__, __perms_publicas__),
        (materia.Autoria, __base__, __perms_publicas__),

        (materia.Proposicao, ['detail_proposicao_enviada',
                              'detail_proposicao_devolvida',
                              'detail_proposicao_incorporada'], set()),  # TODO: tratar em sapl.api questão de que proposições incorporadas serem públicas
        (materia.HistoricoProposicao, __base__, set()),
        (compilacao.TextoArticulado, ['view_restricted_textoarticulado'], __perms_publicas__)
    ]
}
