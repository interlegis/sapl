
from sapl.materia import models as materia
from sapl.protocoloadm import models as protocoloadm
from sapl.rules import SAPL_GROUP_ADMINISTRATIVO, __base__, __perms_publicas__

rules_group_administrativo = {
    'group': SAPL_GROUP_ADMINISTRATIVO,
    'rules': [
        (materia.MateriaLegislativa, [
         'can_access_impressos'], __perms_publicas__),
        (protocoloadm.DocumentoAdministrativo, __base__, set()),
        (protocoloadm.Anexado, __base__, set()),
        (protocoloadm.DocumentoAcessorioAdministrativo, __base__, set()),
        (protocoloadm.TramitacaoAdministrativo, __base__, set()),
        (protocoloadm.VinculoDocAdminMateria, __base__, set())
    ]
}
