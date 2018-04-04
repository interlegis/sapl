
from django.contrib.contenttypes.fields import GenericForeignKey

from sapl.base.models import AppConfig, Autor, CasaLegislativa, TipoAutor
from sapl.comissoes.models import \
    DocumentoAcessorio as DocumentoAcessorioComissoes
from sapl.comissoes.models import Comissao, Composicao, Participacao, Reuniao
from sapl.materia.models import (AcompanhamentoMateria, DocumentoAcessorio,
                                 MateriaLegislativa, Proposicao,
                                 TipoMateriaLegislativa, TipoProposicao,
                                 Tramitacao)
from sapl.norma.models import (NormaJuridica, NormaRelacionada,
                               TipoVinculoNormaJuridica)
from sapl.parlamentares.models import (Frente, Mandato, Parlamentar, Partido,
                                       TipoAfastamento, Votante)
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import (Bancada, Bloco, CargoBancada,
                                ExpedienteMateria, Orador, OradorExpediente,
                                OrdemDia, RegistroVotacao, ResumoOrdenacao,
                                SessaoPlenaria, TipoResultadoVotacao,
                                VotoParlamentar)

from .migracao_dados import appconfs, get_renames, legacy_app

RENAMING_IGNORED_MODELS = [
    Votante, Frente, Bancada, CargoBancada, Bloco,  # parlamentares
    Composicao, Reuniao,  DocumentoAcessorioComissoes,  # commissoes
    AppConfig, CasaLegislativa,  # base
    ResumoOrdenacao,  # sessao
    TipoVinculoNormaJuridica,  # norma

]

RENAMING_IGNORED_FIELDS = [
    (TipoAfastamento, {'indicador'}),
    (Participacao, {'composicao'}),
    (Proposicao, {
        'ano', 'content_type', 'object_id', 'conteudo_gerado_related',
        'status', 'hash_code', 'texto_original'}),
    (TipoProposicao, {
        'object_id', 'content_type',  'tipo_conteudo_related', 'perfis',
        # não estou entendendo como esses campos são enumerados,
        # mas eles não fazem parte da migração
        # 'tipomaterialegislativa_set', 'tipodocumento_set',
    }),

    (Tramitacao, {'ultima'}),
    (SessaoPlenaria, {'finalizada', 'iniciada', 'painel_aberto', 'interativa',
                      'upload_ata',
                      'upload_anexo',
                      'upload_pauta'}),
    (ExpedienteMateria, {'votacao_aberta'}),
    (OrdemDia, {'votacao_aberta'}),
    (NormaJuridica, {'texto_integral', 'data_ultima_atualizacao', 'assuntos'}),
    (Parlamentar, {
        'uf_residencia', 'municipio_residencia', 'cropping', 'fotografia'}),
    (Partido, {'logo_partido'}),
    (MateriaLegislativa, {
        'autores', 'anexadas', 'data_ultima_atualizacao', 'texto_original'}),
    (DocumentoAdministrativo, {'protocolo', 'texto_integral'}),
    (Mandato, {'titular', 'data_fim_mandato', 'data_inicio_mandato'}),
    (TipoMateriaLegislativa, {'sequencia_numeracao'}),
    (TipoAutor, {'content_type'}),
    (TipoResultadoVotacao, {'natureza'}),
    (RegistroVotacao, {'ordem', 'expediente'}),
    (DocumentoAcessorio, {'arquivo', 'data_ultima_atualizacao'}),
    (OradorExpediente, {'upload_anexo', 'observacao'}),
    (Orador, {'upload_anexo', 'observacao'}),
    (VotoParlamentar, {'user', 'ip', 'expediente', 'data_hora', 'ordem'}),
    (NormaRelacionada, {'tipo_vinculo'}),
    (AcompanhamentoMateria, {'confirmado', 'data_cadastro', 'usuario'}),
    (Autor, {'user', 'content_type', 'object_id', 'autor_related'}),
    (Comissao, {'ativa'}),
]


def test_get_renames():
    field_renames, model_renames = get_renames()
    all_models = {m for ac in appconfs for m in ac.get_models()}
    for model in all_models:
        field_names = {f.name for f in model._meta.get_fields()
                       if f.name != 'id'
                       and (f.concrete or isinstance(f, GenericForeignKey))}
        if model not in field_renames:
            # check ignored models in renaming
            assert model in RENAMING_IGNORED_MODELS
        else:
            renamed = set(field_renames[model].keys())

            match_msg_template = 'All %s field names mentioned in renames ' \
                'must match a %s field'

            # all renamed field references correspond to a current field
            assert renamed <= field_names, \
                match_msg_template % ('new', 'current')

            # ignored fields are explicitly listed
            missing = field_names - renamed
            if missing:
                assert (model, missing) in RENAMING_IGNORED_FIELDS, \
                    'Campos faltando na renomeação,' \
                    'mas não listados explicitamente: ({}, {})'.format(
                        model.__name__, missing)

            # all old names correspond to a legacy field
            legacy_model = legacy_app.get_model(
                model_renames.get(model, model.__name__))
            legacy_field_names = {f.name for f in legacy_model._meta.fields}
            assert set(field_renames[model].values()) <= legacy_field_names, \
                match_msg_template % ('old', 'legacy')
