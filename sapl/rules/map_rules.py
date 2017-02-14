from sapl.base import models as base
from sapl.comissoes import models as comissoes
from sapl.compilacao import models as compilacao
from sapl.lexml import models as lexml
from sapl.materia import models as materia
from sapl.norma import models as norma
from sapl.painel import models as painel
from sapl.parlamentares import models as parlamentares
from sapl.protocoloadm import models as protocoloadm
from sapl.rules import (SAPL_GROUP_ADMINISTRATIVO, SAPL_GROUP_ANONYMOUS,
                        SAPL_GROUP_AUTOR, SAPL_GROUP_COMISSOES,
                        SAPL_GROUP_GERAL, SAPL_GROUP_LOGIN_SOCIAL,
                        SAPL_GROUP_MATERIA, SAPL_GROUP_NORMA,
                        SAPL_GROUP_PAINEL, SAPL_GROUP_PARLAMENTAR,
                        SAPL_GROUP_PROTOCOLO, SAPL_GROUP_SESSAO,
                        RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE,
                        SAPL_GROUP_VOTANTE)

from sapl.sessao import models as sessao

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

__base__ = [RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE]
__listdetailchange__ = [RP_LIST, RP_DETAIL, RP_CHANGE]


rules_group_administrativo = {
    'group': SAPL_GROUP_ADMINISTRATIVO,
    'rules': [
        (protocoloadm.DocumentoAdministrativo, __base__),
        (protocoloadm.DocumentoAcessorioAdministrativo, __base__),
        (protocoloadm.TramitacaoAdministrativo, __base__),
    ]
}

rules_group_protocolo = {
    'group': SAPL_GROUP_PROTOCOLO,
    'rules': [
        (protocoloadm.Protocolo, __base__ + [
            'action_anular_protocolo']),
        (protocoloadm.DocumentoAdministrativo,
         [RP_ADD] + __listdetailchange__),
        (protocoloadm.DocumentoAcessorioAdministrativo, __listdetailchange__),

        (materia.MateriaLegislativa, __listdetailchange__),
        (materia.DocumentoAcessorio, __listdetailchange__),
        (materia.Anexada, __base__),
        (materia.Autoria, __base__),

        (materia.Proposicao, ['detail_proposicao_enviada',
                              'detail_proposicao_devolvida',
                              'detail_proposicao_incorporada']),
        (compilacao.TextoArticulado, ['view_restricted_textoarticulado'])
    ]
}

rules_group_comissoes = {
    'group': SAPL_GROUP_COMISSOES,
    'rules': [
        (comissoes.Comissao, __base__),
        (comissoes.Composicao, __base__),
        (comissoes.Participacao, __base__),
    ]
}

rules_group_materia = {
    'group': SAPL_GROUP_MATERIA,
    'rules': [
        (materia.Anexada, __base__),
        (materia.Autoria, __base__),
        (materia.DespachoInicial, __base__),
        (materia.DocumentoAcessorio, __base__),

        (materia.MateriaLegislativa, __base__),
        (materia.Numeracao, __base__),
        (materia.Relatoria, __base__),
        (materia.Tramitacao, __base__),
        (materia.Relatoria, __base__),
        (norma.LegislacaoCitada, __base__),
        (compilacao.Dispositivo, __base__ + [
            'change_dispositivo_edicao_dinamica',

            # TODO: adicionar 'change_dispositivo_registros_compilacao'
            # quando testes forem feitos para permtir que matérias possam
            # ser vinculadas a outras matérias via registro de compilação.
            # Normalmente emendas e/ou projetos substitutivos podem alterar
            # uma matéria original. Fazer esse registro de compilação ofereceria
            # um autografo eletrônico pronto para ser convertido em Norma.
        ])
    ]
}

rules_group_norma = {
    'group': SAPL_GROUP_NORMA,
    'rules': [
        (norma.NormaJuridica, __base__),
        (norma.NormaRelacionada, __base__),

        # Publicacao está com permissão apenas para norma e não para matéria
        # e proposições apenas por análise do contexto, não é uma limitação
        # da ferramenta.
        (compilacao.Publicacao, __base__),
        (compilacao.Vide, __base__),
        (compilacao.Nota, __base__),
        (compilacao.Dispositivo, __base__ + [
            'view_dispositivo_notificacoes',
            'change_dispositivo_edicao_dinamica',
            'change_dispositivo_edicao_avancada',
            'change_dispositivo_registros_compilacao',
            'change_dispositivo_de_vigencia_global'
        ])
    ]
}

rules_group_sessao = {
    'group': SAPL_GROUP_SESSAO,
    'rules': [
        (sessao.SessaoPlenaria, __base__),
        (sessao.SessaoPlenariaPresenca, __base__),
        (sessao.ExpedienteMateria, __base__),
        (sessao.IntegranteMesa, __base__),
        (sessao.ExpedienteSessao, __base__),
        (sessao.Orador, __base__),
        (sessao.OradorExpediente, __base__),
        (sessao.OrdemDia, __base__),
        (sessao.PresencaOrdemDia, __base__),
        (sessao.RegistroVotacao, __base__),
        (sessao.VotoParlamentar, __base__),
    ]
}

rules_group_painel = {
    'group': SAPL_GROUP_PAINEL,
    'rules': [
        (painel.Painel, __base__),
        (painel.Cronometro, __base__),
    ]
}

rules_group_autor = {
    'group': SAPL_GROUP_AUTOR,
    'rules': [
        (materia.Proposicao, __base__),
        (compilacao.Dispositivo, __base__ + [
            'change_your_dispositivo_edicao_dinamica',
        ])
    ]
}

rules_group_parlamentar = {
    'group': SAPL_GROUP_PARLAMENTAR,
    'rules': []
}

rules_group_votante = {
    'group': SAPL_GROUP_VOTANTE,
    'rules': [
        (parlamentares.Votante, ['can_vote'])
    ]
}

rules_group_geral = {
    'group': SAPL_GROUP_GERAL,
    'rules': [
        (base.AppConfig, __base__ + [
            'menu_sistemas',
            'view_tabelas_auxiliares'
        ]),

        (base.CasaLegislativa, __listdetailchange__),
        (base.ProblemaMigracao, []),
        (base.TipoAutor, __base__),
        (base.Autor, __base__),

        (protocoloadm.StatusTramitacaoAdministrativo, __base__),
        (protocoloadm.TipoDocumentoAdministrativo, __base__),

        (comissoes.CargoComissao, __base__),
        (comissoes.TipoComissao, __base__),
        (comissoes.Periodo, __base__),

        (materia.AssuntoMateria, __base__),  # não há implementação
        (materia.MateriaAssunto, __base__),  # não há implementação
        (materia.TipoProposicao, __base__),
        (materia.TipoMateriaLegislativa, __base__),
        (materia.RegimeTramitacao, __base__),
        (materia.Origem, __base__),
        (materia.TipoDocumento, __base__),
        (materia.Orgao, __base__),
        (materia.TipoFimRelatoria, __base__),
        (materia.Parecer, __base__),
        (materia.StatusTramitacao, __base__),
        (materia.UnidadeTramitacao, __base__),

        (norma.AssuntoNorma, __base__),
        (norma.TipoNormaJuridica, __base__),
        (norma.VinculoNormaJuridica, __base__),

        (parlamentares.Legislatura, __base__),
        (parlamentares.SessaoLegislativa, __base__),
        (parlamentares.Coligacao, __base__),
        (parlamentares.ComposicaoColigacao, __base__),
        (parlamentares.Partido, __base__),
        (parlamentares.Municipio, __base__),
        (parlamentares.NivelInstrucao, __base__),
        (parlamentares.SituacaoMilitar, __base__),
        (parlamentares.Parlamentar, __base__),
        (parlamentares.TipoDependente, __base__),
        (parlamentares.Dependente, __base__),
        (parlamentares.Filiacao, __base__),
        (parlamentares.TipoAfastamento, __base__),
        (parlamentares.Mandato, __base__),
        (parlamentares.CargoMesa, __base__),
        (parlamentares.ComposicaoMesa, __base__),
        (parlamentares.Frente, __base__),
        (parlamentares.Votante, __base__),

        (sessao.CargoBancada, __base__),
        (sessao.Bancada, __base__),
        (sessao.TipoSessaoPlenaria, __base__),
        (sessao.TipoResultadoVotacao, __base__),
        (sessao.TipoExpediente, __base__),
        (sessao.Bloco, __base__),

        (lexml.LexmlProvedor, __base__),
        (lexml.LexmlPublicador, __base__),

        (compilacao.VeiculoPublicacao, __base__),
        (compilacao.TipoTextoArticulado, __base__),
        (compilacao.TipoNota, __base__),
        (compilacao.TipoVide, __base__),
        (compilacao.TipoPublicacao, __base__),

        # este model é um espelho do model integrado e sua edição pode
        # confundir Autores, operadores de matéria e/ou norma.
        # Por isso está adicionado apenas para o operador geral
        (compilacao.TextoArticulado,
         __base__ + ['lock_unlock_textoarticulado']),

        # estes tres models são complexos e a principio apenas o admin tem perm
        (compilacao.TipoDispositivo, []),
        (compilacao.TipoDispositivoRelationship, []),
        (compilacao.PerfilEstruturalTextoArticulado, []),






    ]
}


# não possui efeito e é usada nos testes que verificam se todos os models estão
# neste arquivo rules.py
rules_group_anonymous = {
    'group': SAPL_GROUP_ANONYMOUS,
    'rules': [
        (materia.AcompanhamentoMateria, [RP_ADD, RP_DELETE]),
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
                              rules_group_materia['rules'] +
                              rules_group_norma['rules'] +
                              rules_group_sessao['rules'] +
                              rules_group_painel['rules'] +
                              rules_group_login_social['rules'])


rules_patterns = [
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
