from django.utils.translation import ugettext_lazy as _

from sapl.crud import build_crud

from .models import (CargoMesa, Coligacao, Dependente, Filiacao, Legislatura,
                     Mandato, NivelInstrucao, Parlamentar, Partido,
                     SessaoLegislativa, SituacaoMilitar, TipoAfastamento,
                     TipoDependente)

cargo_mesa_crud = build_crud(
    CargoMesa,

    [_('Cargo na Mesa'),
     [('descricao', 10),
      ('unico', 2)]],
)

legislatura_crud = build_crud(
    Legislatura,

    [_('Legislatura'),
     [('id', 3),
      ('data_inicio', 2),
      ('data_fim', 2),
      ('data_eleicao', 2)],
     [('data_inicio', 4), ('data_fim', 4), ('data_eleicao', 4)]],
)

coligacao_crud = build_crud(
    Coligacao,

    [_('Coligação'),
     [('nome', 3),
      ('legislatura', 3),
      ('numero_votos', 3)]],
)

partido_crud = build_crud(
    Partido,

    [_('Partido Político'),
     [('nome', 6),
      ('sigla', 2),
      ('data_criacao', 2),
      ('data_extincao', 2)]],
)

dependente_crud = build_crud(
    Dependente,

    [_('Dependentes'),
     [('nome', 12)],
     [('tipo', 4), ('sexo', 4), ('data_nascimento', 4)],
     [('cpf', 4), ('rg', 4), ('titulo_eleitor', 4)]],
)

sessao_legislativa_crud = build_crud(
    SessaoLegislativa,

    [_('Sessão Legislativa'),
     [('numero', 2),
      ('tipo', 2),
      ('data_inicio', 2),
      ('data_fim', 2),
      ('data_inicio_intervalo', 2),
      ('data_fim_intervalo', 2)]],
)

dependente_crud = build_crud(
    Parlamentar,

    [_('Cadastro do Parlamentar'),
     [('nome_parlamentar', 4), ('login_FIXME', 4), ('ativo', 4)],
     [('nome_completo', 12)],
     [('nivel_instrucao', 4), ('sexo', 4), ('data_nascimento', 4)],
     [('cpf', 4), ('rg', 4), ('titulo_eleitor', 4)],
     [('situacao_militar', 6), ('profissao', 6)],
     [('endereco_web', 12)],
     [('email', 12)],
     [('numero_gab_parlamentar', 4), ('telefone', 4), ('fax', 4)],
     [('endereco_residencia', 6), ('cep_residencia', 6)],
     [('municipio_residencia', 6), ('uf_FIXME', 6)],
     [('telefone_residencia', 6), ('fax_residencia', 6)],
     [('locais_atuacao', 12)],
     [('file_FIXME', 12)],
     [('biografia', 12)],
     [('observacao_FIXME', 12)],
     [('parlamentar_salvar_FIXME', 12)]],
)

filiacao_crud = build_crud(
    Filiacao,

    [_('Filiações Partidárias '),
     [('partido', 4), ('data', 4), ('data_desfiliacao', 4)]],
)

mandato_crud = build_crud(
    Mandato,

    [_('Mandato'),
     [('legislatura', 4), ('coligacao', 4), ('votos_recebidos', 4)],
     [('ind_titular_FIXME', 3),
      ('dat_inicio_mandato_FIXME', 3),
      ('data_fim_mandato', 3),
      ('data_expedicao_diploma', 3)],
     [('observacao', 12)]],
)

tipo_dependente_crud = build_crud(
    TipoDependente,

    [_('Tipo de Dependente'),
     [('descricao', 12)]],
)

nivel_instrucao_crud = build_crud(
    NivelInstrucao,

    [_('Nível Instrução'),
     [('descricao', 12)]],
)

tipo_afastamento_crud = build_crud(
    TipoAfastamento,

    [_('Tipo de Afastamento'),
     [('descricao', 6), ('dispositivo', 6)],
     [('afastamento', 6)]],
)

tipo_militar_crud = build_crud(
    SituacaoMilitar,

    [_('Tipo Situação Militar'),
     [('descricao', 12)]],
)
