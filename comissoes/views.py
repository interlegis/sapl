from django.utils.translation import ugettext_lazy as _

from comissoes.models import TipoComissao, Comissao
from sapl.crud import build_crud


tipo_comissao_crud = build_crud(
    TipoComissao,

    [_('Tipo Comissão'),
     [('nome', 3), ('sigla', 2)],
     [('dispositivo_regimental', 2), ('natureza', 2)],
     ],
)

comissao_crud = build_crud(
    Comissao,

    [_('Dados Básicos'),
     [('nome', 9), ('sigla', 3)],
     [('tipo', 3),
      ('data_criacao', 3),
      ('unidade_deliberativa', 3),
      ('data_extincao', 3)]],

    [_('Dados Complementares'),
     [('local_reuniao', 4),
      ('agenda_reuniao', 4),
      ('telefone_reuniao', 4)],
     [('endereco_secretaria', 4),
      ('telefone_secretaria', 4),
      ('fax_secretaria', 4)],
     [('secretario', 4), ('email', 8)],
     [('finalidade', 12)]],

    [_('Temporária'),
     [('apelido_temp', 8),
      ('data_instalacao_temp', 4)],
     [('data_final_prevista_temp', 4),
      ('data_prorrogada_temp', 4),
      ('data_fim_comissao', 4)]],
)
