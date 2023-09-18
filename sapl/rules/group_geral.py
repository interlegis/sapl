from django.contrib.contenttypes import models as contenttypes

from sapl.audiencia import models as audiencia
from sapl.base import models as base
from sapl.comissoes import models as comissoes
from sapl.compilacao import models as compilacao
from sapl.lexml import models as lexml
from sapl.materia import models as materia
from sapl.norma import models as norma
from sapl.parlamentares import models as parlamentares
from sapl.protocoloadm import models as protocoloadm
from sapl.rules import SAPL_GROUP_GERAL, RP_ADD, __base__, __perms_publicas__, \
    __listdetailchange__
from sapl.sessao import models as sessao


rules_group_geral = {
    'group': SAPL_GROUP_GERAL,
    'rules': [
        (base.AppConfig, __base__ + [
            'menu_sistemas',
            'view_tabelas_auxiliares'
        ], set()),

        (base.CasaLegislativa, __listdetailchange__ +
         [RP_ADD], __perms_publicas__),
        (base.TipoAutor, __base__, __perms_publicas__),
        (base.Autor, __base__, __perms_publicas__),
        (base.OperadorAutor, __base__, __perms_publicas__),
        (base.AuditLog, __base__, set()),
        (base.Metadata, __base__, set()),

        (protocoloadm.StatusTramitacaoAdministrativo, __base__, set()),
        (protocoloadm.TipoDocumentoAdministrativo, __base__, set()),

        (comissoes.CargoComissao, __base__, __perms_publicas__),
        (comissoes.TipoComissao, __base__, __perms_publicas__),
        (comissoes.Periodo, __base__, __perms_publicas__),

        (materia.AssuntoMateria, __base__,
         __perms_publicas__),
        (materia.MateriaAssunto, __base__,
         __perms_publicas__),
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
        (materia.ConfigEtiquetaMateriaLegislativa, __base__, set()),

        (norma.AssuntoNorma, __base__, __perms_publicas__),
        (norma.TipoNormaJuridica, __base__, __perms_publicas__),
        (norma.TipoVinculoNormaJuridica, __base__, __perms_publicas__),
        (norma.NormaEstatisticas, __base__, __perms_publicas__),

        (parlamentares.Legislatura, __base__, __perms_publicas__),
        (parlamentares.SessaoLegislativa, __base__, __perms_publicas__),
        (parlamentares.Coligacao, __base__, __perms_publicas__),
        (parlamentares.ComposicaoColigacao, __base__, __perms_publicas__),
        (parlamentares.Partido, __base__, __perms_publicas__),
        (parlamentares.NivelInstrucao, __base__, __perms_publicas__),
        (parlamentares.MesaDiretora, __base__, __perms_publicas__),
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
        (parlamentares.FrenteCargo, __base__, __perms_publicas__),
        (parlamentares.FrenteParlamentar, __base__, __perms_publicas__),
        (parlamentares.Votante, __base__, __perms_publicas__),
        (parlamentares.Bloco, __base__, __perms_publicas__),
        (parlamentares.BlocoCargo, __base__, __perms_publicas__),
        (parlamentares.BlocoMembro, __base__, __perms_publicas__),

        (sessao.CargoBancada, __base__, __perms_publicas__),
        (sessao.Bancada, __base__, __perms_publicas__),
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
        (compilacao.TipoDispositivo, __listdetailchange__, __perms_publicas__),
        (compilacao.TipoDispositivoRelationship, [], set()),
        (compilacao.PerfilEstruturalTextoArticulado, [], set()),

        (audiencia.AudienciaPublica, __base__, __perms_publicas__),
        (audiencia.TipoAudienciaPublica, __base__, __perms_publicas__),

        # permite consulta anônima pela api a lista de contenttypes
        (contenttypes.ContentType, [], __perms_publicas__),

    ]
}
