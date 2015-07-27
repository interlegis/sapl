from django.utils.translation import ugettext_lazy as _

from sapl.crud import build_crud

from .models import (Anexada, Autor, Autoria, DocumentoAcessorio,
                     MateriaLegislativa, Numeracao, Orgao, Origem, Proposicao,
                     RegimeTramitacao, Relatoria, StatusTramitacao, TipoAutor,
                     TipoDocumento, TipoFimRelatoria, TipoMateriaLegislativa,
                     TipoProposicao, Tramitacao, UnidadeTramitacao)

origem_crud = build_crud(
    Origem,

    [_('Origem'),
     [('nome', 8), ('sigla', 4)]],
)

tipo_materia_crud = build_crud(
    TipoMateriaLegislativa,

    [_('Tipo Matéria Legislativa'),
     [('sigla', 4), ('descricao', 8)]],
)

regime_tramitacao_crud = build_crud(
    RegimeTramitacao,

    [_('Tipo de Documento'),
     [('descricao', 12)]],
)

tipo_documento_crud = build_crud(
    TipoDocumento,

    [_('Regime Tramitação'),
     [('descricao', 12)]],
)

tipo_fim_relatoria_crud = build_crud(
    TipoFimRelatoria,

    [_('Tipo Fim de Relatoria'),
     [('descricao', 12)]],
)

materia_legislativa_crud = build_crud(
    MateriaLegislativa,

    [_('Identificação Básica'),
     [('tipo', 4), ('numero', 4), ('ano', 4)],
     [('data_apresentacao', 4),
      ('num_protocolo_spdo_FIXME', 4),
      ('tipo_apresentacao', 4)],
     [('nom_arquivo_FIXME', 6), ('modelo_FIXME', 6)]],

    [_('Proposição Eletrônica')],

    [_('Outras Informações'),
     [('apelido', 4), ('dias_prazo', 4), ('polemica', 4)],
     [('objeto', 4), ('regime_tramitacao', 4), ('em_tramitacao', 4)],
     [('data_fim_prazo', 3),
      ('data_publicacao', 3),
      ('complementar', 3),
      ('txt_cep_FIXME', 3)]],

    [_('Origem Externa'),
     [('tipo_origem_externa', 4),
      ('numero_origem_externa', 4),
      ('ano_origem_externa', 4)],
     [('local_origem_externa', 6), ('data_origem_externa', 6)]],

    [_('Dados Textuais'),
     [('ementa', 12)],
     [('indexacao', 12)],
     [('observacao', 12)]],
)

Anexada_crud = build_crud(
    Anexada,

    [_('Matéria Legislativa'),
     [('tip_id_basica_FIXME', 4),
      ('num_ident_basica_FIXME', 4),
      ('ano_ident_basica_FIXME', 4)],
     [('data_anexacao', 6), ('data_desanexacao', 6)]],

    [_('Matéria Anexada'),
     [('tip_id_basica_FIXME', 4),
      ('num_ident_basica_FIXME', 4),
      ('ano_ident_basica_FIXME', 4)],
     [('data_anexacao', 6), ('data_desanexacao', 6)]],
)

tipo_autor_crud = build_crud(
    TipoAutor,

    [_('Tipo Autor'),
     [('descricao', 4)]],
)


autor_crud = build_crud(
    Autor,

    [_('Autor'),
     [('tipo', 3), ('nome', 9)],
     [('username', 12)]],
)

autoria_crud = build_crud(
    Autoria,

    [_('Autoria'),
     [('tip_autor_FIXME', 4),
      ('nom_autor_FIXME', 4),
      ('primeiro_autor', 4)]],
)

documento_acessorio_crud = build_crud(
    DocumentoAcessorio,

    [_('Documento Acessório'),
     [('tipo', 6), ('nome', 6)],
     [('data', 6), ('autor', 6)],
     [('nom_arquivo_FIXME', 12)],
     [('ementa', 12)],
     [('txt_observacao_FIXME', 12)]],
)

numeracao_crud = build_crud(
    Numeracao,

    [_('Numeração'),
     [('tipo_materia', 6), ('numero_materia', 6)],
     [('ano_materia', 6), ('data_materia', 6)]],
)

orgao_crud = build_crud(
    Orgao,

    [_('Órgão'),
     [('nome', 4),
      ('sigla', 2),
      ('telefone', 2),
      ('endereco', 2),
      ('unidade_deliberativa', 2)]],
)

relatoria_crud = build_crud(
    Relatoria,

    [_('Relatoria'),
     [('data_designacao_relator', 12)],
     [('dados_FIXME', 12)],
     [('data_destituicao_relator', 6), ('tipo_fim_relatoria', 6)]],
)

tipo_proposicao_crud = build_crud(
    TipoProposicao,

    [_('Tipo Proposição'),
     [('descricao', 12)],
     [('materia_ou_documento', 4), ('tipo_documento', 8)],
     [('modelo', 12)]],
)

proposicao_crud = build_crud(
    Proposicao,

    [_('Proposição'),
     [('tipo', 4), ('dat_criacao_FIXME', 4), ('data_recebimento', 4)],
     [('descricao_FIXME', 12)],
     [('tip_id_basica_FIXME', 4),
      ('num_ident_basica_FIXME', 4),
      ('ano_ident_basica_FIXME', 4)],
     [('nom_arquivo_FIXME', 6), ('modelo_FIXME', 6)]],
)

status_tramitacao_crud = build_crud(
    StatusTramitacao,

    [_('Status Tramitação'),
     [('sigla', 4),
      ('indicador', 4),
      ('descricao', 4)]],
)

unidade_tramitacao_crud = build_crud(
    UnidadeTramitacao,

    [_('Unidade Tramitação'),
     [('orgao', 12)],
     [('comissao', 12)],
     [('parlamentar', 12)]],
)

tramitacao_crud = build_crud(
    Tramitacao,

    [_('Tramitação'),
     [('cod_ult_tram_dest_FIXME', 6), ('unidade_tramitacao_local', 6)],
     [('status', 4), ('turno', 4), ('urgente', 4)],
     [('unidade_tramitacao_destino', 4),
      ('data_encaminhamento', 4),
      ('data_fim_prazo', 4)],
     [('texto', 12)]],
)
