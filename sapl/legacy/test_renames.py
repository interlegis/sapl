import sapl.comissoes
import sapl.materia
import sapl.norma
import sapl.sessao

from .migration import appconfs, get_renames, legacy_app

RENAMING_IGNORED_MODELS = [
    sapl.comissoes.models.Composicao,
    sapl.norma.models.AssuntoNormaRelationship,

    # FIXME retirar daqui depois que a issue #218 for resolvida!!!!!!!
    sapl.sessao.models.AcompanharMateria,
]

RENAMING_IGNORED_FIELDS = [
    (sapl.comissoes.models.Participacao, {'composicao'}),
    (sapl.materia.models.Proposicao, {'documento'}),
    (sapl.materia.models.TipoProposicao, {'tipo_documento'}),
    (sapl.materia.models.Tramitacao, {'ultima'}),
    (sapl.sessao.models.SessaoPlenaria, {'finalizada',
                                         'upload_pauta',
                                         'upload_ata',
                                         'iniciada'}),
    (sapl.sessao.models.ExpedienteMateria, {'votacao_aberta'}),
    (sapl.sessao.models.OrdemDia, {'votacao_aberta'}),
]


def test_get_renames():
    field_renames, model_renames = get_renames()
    all_models = {m for ac in appconfs for m in ac.get_models()}
    for model in all_models:
        field_names = {f.name for f in model._meta.fields if f.name != 'id'}
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
            missing_in_renames = field_names - renamed
            if missing_in_renames:
                assert (model, missing_in_renames) in \
                    RENAMING_IGNORED_FIELDS, \
                    'Field(s) missing in renames but not explicitly listed'

            # all old names correspond to a legacy field
            legacy_model = legacy_app.get_model(
                model_renames.get(model, model.__name__))
            legacy_field_names = {f.name for f in legacy_model._meta.fields}
            assert set(field_renames[model].values()) <= legacy_field_names, \
                match_msg_template % ('old', 'legacy')
