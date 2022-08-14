
from sapl.rules import SAPL_GROUP_SESSAO, __perms_publicas__, __base__
from sapl.sessao import models as sessao

rules_group_sessao = {
    'group': SAPL_GROUP_SESSAO,
    'rules': [
        (sessao.SessaoPlenaria, __base__, __perms_publicas__),
        (sessao.SessaoPlenariaPresenca, __base__, __perms_publicas__),
        (sessao.ExpedienteMateria, __base__, __perms_publicas__),
        (sessao.OcorrenciaSessao, __base__, __perms_publicas__),
        (sessao.IntegranteMesa, __base__, __perms_publicas__),
        (sessao.ExpedienteSessao, __base__, __perms_publicas__),
        (sessao.Orador, __base__, __perms_publicas__),
        (sessao.OradorExpediente, __base__, __perms_publicas__),
        (sessao.OradorOrdemDia, __base__, __perms_publicas__),
        (sessao.OrdemDia, __base__, __perms_publicas__),
        (sessao.PresencaOrdemDia, __base__, __perms_publicas__),
        (sessao.RegistroVotacao, __base__, __perms_publicas__),
        (sessao.VotoParlamentar, __base__, __perms_publicas__),
        (sessao.JustificativaAusencia, __base__, __perms_publicas__),
        (sessao.RetiradaPauta, __base__, __perms_publicas__),
        (sessao.RegistroLeitura, __base__, __perms_publicas__),
        (sessao.ConsideracoesFinais, __base__, __perms_publicas__),
        (sessao.Correspondencia, __base__, __perms_publicas__)
    ]
}
