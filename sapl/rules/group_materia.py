
from sapl.compilacao import models as compilacao
from sapl.materia import models as materia
from sapl.norma import models as norma
from sapl.rules import SAPL_GROUP_MATERIA, __base__, __perms_publicas__

rules_group_materia = {
    'group': SAPL_GROUP_MATERIA,
    'rules': [
        (materia.Anexada, __base__, __perms_publicas__),
        (materia.Autoria, __base__, __perms_publicas__),
        (materia.DespachoInicial, __base__, __perms_publicas__),
        (materia.DocumentoAcessorio, __base__, __perms_publicas__),
        (materia.MateriaAssunto, __base__, __perms_publicas__),
        (materia.AssuntoMateria, __base__, __perms_publicas__),

        (materia.MateriaLegislativa, __base__ +
         ['can_access_impressos'], __perms_publicas__),
        (materia.Numeracao, __base__, __perms_publicas__),
        (materia.Tramitacao, __base__, __perms_publicas__),
        (materia.MateriaEmTramitacao, __base__, __perms_publicas__),
        (norma.LegislacaoCitada, __base__, __perms_publicas__),
        (norma.AutoriaNorma, __base__, __perms_publicas__),
        (compilacao.Dispositivo, __base__ + [
            'change_dispositivo_edicao_dinamica',

            # TODO: adicionar 'change_dispositivo_registros_compilacao'
            # quando testes forem feitos para permtir que matérias possam
            # ser vinculadas a outras matérias via registro de compilação.
            # Normalmente emendas e/ou projetos substitutivos podem alterar
            # uma matéria original.
            # Fazer esse registro de compilação ofereceria
            # um autografo eletrônico pronto para ser convertido em Norma.
        ], __perms_publicas__)
    ]
}
