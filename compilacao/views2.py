from django.utils.translation import ugettext_lazy as _

from compilacao.models import (PerfilEstruturalTextoArticulado,
                               TipoDispositivo, TipoNota, TipoPublicacao,
                               TipoVide, VeiculoPublicacao)
from sapl.crud import build_crud

DISPOSITIVO_SELECT_RELATED = (
    'tipo_dispositivo',
    'ta_publicado',
    'ta',
    'dispositivo_atualizador',
    'dispositivo_atualizador__dispositivo_pai',
    'dispositivo_atualizador__dispositivo_pai__ta',
    'dispositivo_atualizador__dispositivo_pai__ta__tipo',
    'dispositivo_pai',
    'dispositivo_pai__tipo_dispositivo')

tipo_nota_crud = build_crud(
    TipoNota, 'tipo_nota', [

        [_('Tipo da Nota'),
         [('sigla', 2), ('nome', 10)],
         [('modelo', 12)]],
    ])

tipo_vide_crud = build_crud(
    TipoVide, 'tipo_vide', [

        [_('Tipo de Vide'),
         [('sigla', 2), ('nome', 10)]],
    ])

tipo_publicacao_crud = build_crud(
    TipoPublicacao, 'tipo_publicacao', [

        [_('Tipo de Publicação'),
         [('sigla', 2), ('nome', 10)]],
    ])

perfil_estr_txt_norm = build_crud(
    PerfilEstruturalTextoArticulado, 'perfil_estrutural', [

        [_('Perfil Estrutural de Textos Articulados'),
         [('sigla', 2), ('nome', 10)]],
    ])


veiculo_publicacao_crud = build_crud(
    VeiculoPublicacao, 'veiculo_publicacao', [

        [_('Veículo de Publicação'),
         [('sigla', 2), ('nome', 10)]],
    ])

tipo_dispositivo_crud = build_crud(
    TipoDispositivo, 'tipo_dispositivo', [

        [_('Dados Básicos'),
         [('nome', 8), ('class_css', 4)]],

        [_('Configurações para Edição do Rótulo'),
         [('rotulo_prefixo_texto', 3),
          ('rotulo_sufixo_texto', 3),
          ('rotulo_ordinal', 3),
          ('contagem_continua', 3)],

         ],

        [_('Configurações para Renderização de Rótulo e Texto'),
         [('rotulo_prefixo_html', 6),
          ('rotulo_sufixo_html', 6), ],

         [('texto_prefixo_html', 4),
          ('dispositivo_de_articulacao', 4),
          ('texto_sufixo_html', 4)],
         ],

        [_('Configurações para Nota Automática'),
         [('nota_automatica_prefixo_html', 6),
          ('nota_automatica_sufixo_html', 6),
          ],
         ],

        [_('Configurações para Variações Numéricas'),

         [('formato_variacao0', 12)],
         [('rotulo_separador_variacao01', 5), ('formato_variacao1', 7), ],
         [('rotulo_separador_variacao12', 5), ('formato_variacao2', 7), ],
         [('rotulo_separador_variacao23', 5), ('formato_variacao3', 7), ],
         [('rotulo_separador_variacao34', 5), ('formato_variacao4', 7), ],
         [('rotulo_separador_variacao45', 5), ('formato_variacao5', 7), ],

         ],

    ])
