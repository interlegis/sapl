"""
Todas as permissões do django framework seguem o padrão

        [app_label].[radical_de_permissao]_[model]

ou seja, em sapl.norma.NormaJuridica, por exemplo, o django framework cria
três permissões registadas na classe Permission:

        definição                         uso

        - add_normajuridica               norma.add_normajuridica
        - change_normajuridica            norma.change_normajuridica
        - delete_normajuridica            norma.delete_normajuridica

No SAPL foram acrescidas em todos os models as duas regras abaixo, adicionadas
com o Signal post_migrate `create_proxy_permissions`
localizado em sapl.rules.apps.py.

        - list_normajuridica              norma.list_normajuridica
        - detail_normajuridica            norma.detail_normajuridica

Tanto o Crud implementado em sapl.crud.base.py quanto o Signal post_migrate
`update_groups` que é responsável por ler o mapa deste
arquivo (sapl.rules.map_rules.py) e criar os grupos definidos na regra de
negócio trabalham com os cinco radiais de permissão
e com qualquer outro tipo de permissão customizada, nesta ordem de precedência.

"""
from sapl.audiencia import models as audiencia
from sapl.base import models as base
from sapl.comissoes import models as comissoes
from sapl.compilacao import models as compilacao
from sapl.lexml import models as lexml
from sapl.materia import models as materia
from sapl.norma import models as norma
from sapl.painel import models as painel
from sapl.parlamentares import models as parlamentares
from sapl.protocoloadm import models as protocoloadm
from sapl.rules import (RP_ADD, RP_CHANGE, RP_DELETE, RP_DETAIL, RP_LIST,
                        SAPL_GROUP_ADMINISTRATIVO, SAPL_GROUP_ANONYMOUS,
                        SAPL_GROUP_AUTOR, SAPL_GROUP_COMISSOES,
                        SAPL_GROUP_GERAL, SAPL_GROUP_LOGIN_SOCIAL,
                        SAPL_GROUP_MATERIA, SAPL_GROUP_NORMA,
                        SAPL_GROUP_PAINEL, SAPL_GROUP_PARLAMENTAR,
                        SAPL_GROUP_PROTOCOLO, SAPL_GROUP_SESSAO,
                        SAPL_GROUP_VOTANTE)
from sapl.sessao import models as sessao


__base__ = [RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE]
__listdetailchange__ = [RP_LIST, RP_DETAIL, RP_CHANGE]

__perms_publicas__ = {RP_LIST, RP_DETAIL}


rules_group_administrativo = {
    'group': SAPL_GROUP_ADMINISTRATIVO,
    'rules': [
        (materia.MateriaLegislativa, [
         'can_access_impressos'], __perms_publicas__),
        # TODO: tratar em sapl.api a questão de ostencivo e restritivo
        (protocoloadm.DocumentoAdministrativo, __base__, set()),
        (protocoloadm.Anexado, __base__, set()),
        (protocoloadm.DocumentoAcessorioAdministrativo, __base__, set()),
        (protocoloadm.TramitacaoAdministrativo, __base__, set()),
    ]
}

rules_group_audiencia = {
    'group': SAPL_GROUP_GERAL,
    'rules': [
        (audiencia.AudienciaPublica, __base__, __perms_publicas__),
        (audiencia.TipoAudienciaPublica, __base__, __perms_publicas__),
        (audiencia.AnexoAudienciaPublica, __base__, __perms_publicas__),
    ]
}


rules_group_protocolo = {
    'group': SAPL_GROUP_PROTOCOLO,
    'rules': [
        (protocoloadm.Protocolo, __base__ + [
            'action_anular_protocolo'], set()),
        (protocoloadm.DocumentoAdministrativo,
         [RP_ADD] + __listdetailchange__, set()),
        (protocoloadm.DocumentoAcessorioAdministrativo, __listdetailchange__, set()),

        (materia.MateriaLegislativa, __listdetailchange__, __perms_publicas__),
        (materia.MateriaLegislativa, [
         'can_access_impressos'], __perms_publicas__),
        (materia.DocumentoAcessorio, __listdetailchange__, __perms_publicas__),
        (materia.Anexada, __base__, __perms_publicas__),
        (materia.Autoria, __base__, __perms_publicas__),

        (materia.Proposicao, ['detail_proposicao_enviada',
                              'detail_proposicao_devolvida',
                              'detail_proposicao_incorporada'], set()),  # TODO: tratar em sapl.api questão de que proposições incorporadas serem públicas
        (compilacao.TextoArticulado, [
         'view_restricted_textoarticulado'], __perms_publicas__)
    ]
}

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
    ]
}

rules_group_painel = {
    'group': SAPL_GROUP_PAINEL,
    'rules': [
        (painel.Painel, __base__, __perms_publicas__),
        (painel.Cronometro, __base__, __perms_publicas__),
    ]
}

rules_group_autor = {
    'group': SAPL_GROUP_AUTOR,
    'rules': [
        (materia.Proposicao, __base__, set()),
        (compilacao.Dispositivo, __base__ + [
            'change_your_dispositivo_edicao_dinamica',
        ], __perms_publicas__)
    ]
}

rules_group_parlamentar = {
    'group': SAPL_GROUP_PARLAMENTAR,
    'rules': []
}

rules_group_votante = {
    'group': SAPL_GROUP_VOTANTE,
    'rules': [
        (parlamentares.Votante, ['can_vote'], set())
    ]
}

rules_group_geral = {
    'group': SAPL_GROUP_GERAL,
    'rules': [
        (base.AppConfig, __base__ + [
            'menu_sistemas',
            'view_tabelas_auxiliares'
        ], set()),

        (painel.PainelConfig, __base__, set()),

        (base.CasaLegislativa, __listdetailchange__ +
         [RP_ADD], __perms_publicas__),
        (base.TipoAutor, __base__, __perms_publicas__),
        (base.Autor, __base__, __perms_publicas__),

        (protocoloadm.StatusTramitacaoAdministrativo, __base__, set()),
        (protocoloadm.TipoDocumentoAdministrativo, __base__, set()),

        (comissoes.CargoComissao, __base__, __perms_publicas__),
        (comissoes.TipoComissao, __base__, __perms_publicas__),
        (comissoes.Periodo, __base__, __perms_publicas__),

        (materia.AssuntoMateria, __base__,
         __perms_publicas__),  # não há implementação
        (materia.MateriaAssunto, __base__,
         __perms_publicas__),  # não há implementação
        (materia.MateriaLegislativa, [
         'can_access_impressos'], __perms_publicas__),
        (materia.TipoProposicao, __base__, __perms_publicas__),
        (materia.TipoMateriaLegislativa, __base__, __perms_publicas__),
        (materia.RegimeTramitacao, __base__, __perms_publicas__),
        (materia.Origem, __base__, __perms_publicas__),
        (materia.TipoDocumento, __base__, __perms_publicas__),
        (materia.Orgao, __base__, __perms_publicas__),
        (materia.TipoFimRelatoria, __base__, __perms_publicas__),
        (materia.Parecer, __base__, __perms_publicas__),
        (materia.StatusTramitacao, __base__, __perms_publicas__),
        (materia.UnidadeTramitacao, __base__, __perms_publicas__),
        

        (norma.AssuntoNorma, __base__, __perms_publicas__),
        (norma.TipoNormaJuridica, __base__, __perms_publicas__),
        (norma.TipoVinculoNormaJuridica, __base__, __perms_publicas__),
        (norma.NormaEstatisticas, __base__, __perms_publicas__),

        (parlamentares.Legislatura, __base__, __perms_publicas__),
        (parlamentares.SessaoLegislativa, __base__, __perms_publicas__),
        (parlamentares.Coligacao, __base__, __perms_publicas__),
        (parlamentares.ComposicaoColigacao, __base__, __perms_publicas__),
        (parlamentares.Partido, __base__, __perms_publicas__),
        (parlamentares.HistoricoPartido, __base__, __perms_publicas__),
        (parlamentares.NivelInstrucao, __base__, __perms_publicas__),
        (parlamentares.SituacaoMilitar, __base__, __perms_publicas__),
        (parlamentares.Parlamentar, __base__, __perms_publicas__),
        (parlamentares.TipoDependente, __base__, __perms_publicas__),
        (parlamentares.Dependente, __base__, __perms_publicas__),
        (parlamentares.Filiacao, __base__, __perms_publicas__),
        (parlamentares.TipoAfastamento, __base__, __perms_publicas__),
        (parlamentares.Mandato, __base__, __perms_publicas__),
        (parlamentares.CargoMesa, __base__, __perms_publicas__),
        (parlamentares.ComposicaoMesa, __base__, __perms_publicas__),
        (parlamentares.Frente, __base__, __perms_publicas__),
        (parlamentares.Votante, __base__, __perms_publicas__),
        (parlamentares.Bancada, __base__, __perms_publicas__),
        (parlamentares.CargoBancada, __base__, __perms_publicas__),
        (parlamentares.Bloco, __base__, __perms_publicas__),
        (parlamentares.CargoBloco, __base__, __perms_publicas__),
        (parlamentares.CargoBlocoPartido, __base__, __perms_publicas__),
        (parlamentares.AfastamentoParlamentar, __base__, __perms_publicas__),

        (sessao.TipoSessaoPlenaria, __base__, __perms_publicas__),
        (sessao.TipoResultadoVotacao, __base__, __perms_publicas__),
        (sessao.TipoExpediente, __base__, __perms_publicas__),
        (sessao.TipoJustificativa, __base__, __perms_publicas__),
        (sessao.JustificativaAusencia, __base__, __perms_publicas__),
        (sessao.ResumoOrdenacao, __base__, __perms_publicas__),
        (sessao.TipoRetiradaPauta, __base__, __perms_publicas__),

        (lexml.LexmlProvedor, __base__, set()),
        (lexml.LexmlPublicador, __base__, set()),

        (compilacao.VeiculoPublicacao, __base__, __perms_publicas__),
        (compilacao.TipoTextoArticulado, __base__, __perms_publicas__),
        (compilacao.TipoNota, __base__, __perms_publicas__),
        (compilacao.TipoVide, __base__, __perms_publicas__),
        (compilacao.TipoPublicacao, __base__, __perms_publicas__),

        # este model é um espelho do model integrado e sua edição pode
        # confundir Autores, operadores de matéria e/ou norma.
        # Por isso está adicionado apenas para o operador geral
        (compilacao.TextoArticulado,
         __base__ + ['lock_unlock_textoarticulado'], set()),

        # estes tres models são complexos e a principio apenas o admin tem perm
        (compilacao.TipoDispositivo, [], set()),
        (compilacao.TipoDispositivoRelationship, [], set()),
        (compilacao.PerfilEstruturalTextoArticulado, [], set()),

        (audiencia.AudienciaPublica, __base__, __perms_publicas__),
        (audiencia.TipoAudienciaPublica, __base__, __perms_publicas__),




    ]
}


# não possui efeito e é usada nos testes que verificam se todos os models estão
# neste arquivo rules.py
rules_group_anonymous = {
    'group': SAPL_GROUP_ANONYMOUS,
    'rules': [
        (materia.AcompanhamentoMateria, [RP_ADD, RP_DELETE], set()),
        (protocoloadm.AcompanhamentoDocumento, [RP_ADD, RP_DELETE], set()),
    ]
}

rules_group_login_social = {
    'group': SAPL_GROUP_LOGIN_SOCIAL,
    'rules': []
}

rules_group_geral['rules'] = (rules_group_geral['rules'] +
                              rules_group_administrativo['rules'] +
                              rules_group_protocolo['rules'] +
                              rules_group_comissoes['rules'] +
                              rules_group_audiencia['rules'] +
                              rules_group_materia['rules'] +
                              rules_group_norma['rules'] +
                              rules_group_sessao['rules'] +
                              rules_group_painel['rules'] +
                              rules_group_login_social['rules'])


rules_patterns = [
    rules_group_audiencia,
    rules_group_administrativo,
    rules_group_protocolo,
    rules_group_comissoes,
    rules_group_materia,
    rules_group_norma,
    rules_group_sessao,
    rules_group_painel,
    rules_group_geral,
    rules_group_autor,
    rules_group_parlamentar,
    rules_group_votante,

    rules_group_anonymous,   # anotação para validação do teste de rules
    rules_group_login_social  # TODO não implementado
]


rules_patterns_public = {}


def _get_registration_key(model):
    return '%s:%s' % (model._meta.app_label, model._meta.model_name)


for rules_group in rules_patterns:
    for rules in rules_group['rules']:
        key = _get_registration_key(rules[0])
        if key not in rules_patterns_public:
            rules_patterns_public[key] = set()

        r = set(map(lambda x, m=rules[0]: '{}{}{}'.format(
            m._meta.app_label,
            x,
            m._meta.model_name), rules[2]))
        rules_patterns_public[key] = rules_patterns_public[key] | r
