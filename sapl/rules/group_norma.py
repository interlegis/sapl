from sapl.compilacao import models as compilacao
from sapl.norma import models as norma
from sapl.rules import SAPL_GROUP_NORMA, __base__, __perms_publicas__

rules_group_norma = {
    'group': SAPL_GROUP_NORMA,
    'rules': [
        (norma.NormaJuridica, __base__, __perms_publicas__),
        (norma.NormaRelacionada, __base__, __perms_publicas__),
        (norma.AnexoNormaJuridica, __base__, __perms_publicas__),
        (norma.AutoriaNorma, __base__, __perms_publicas__),
        (norma.NormaEstatisticas, __base__, __perms_publicas__),

        # Publicacao está com permissão apenas para norma e não para matéria
        # e proposições apenas por análise do contexto, não é uma limitação
        # da ferramenta.
        (compilacao.Publicacao, __base__, __perms_publicas__),
        (compilacao.Vide, __base__, __perms_publicas__),
        (compilacao.Nota, __base__, __perms_publicas__),
        (compilacao.Dispositivo, __base__ + [
            'view_dispositivo_notificacoes',
            'change_dispositivo_edicao_dinamica',
            'change_dispositivo_edicao_avancada',
            'change_dispositivo_registros_compilacao',
            'change_dispositivo_de_vigencia_global'
        ], __perms_publicas__)
    ]
}
