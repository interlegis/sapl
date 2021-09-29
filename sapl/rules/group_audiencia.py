from sapl.audiencia import models as audiencia
from sapl.rules import SAPL_GROUP_AUDIENCIA, __base__, __perms_publicas__
rules_group_audiencia = {
    'group': SAPL_GROUP_AUDIENCIA,
    'rules': [
        (audiencia.AudienciaPublica, __base__, __perms_publicas__),
        (audiencia.TipoAudienciaPublica, __base__, __perms_publicas__),
        (audiencia.AnexoAudienciaPublica, __base__, __perms_publicas__),
    ]
}
