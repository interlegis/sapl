from django.utils.translation import ugettext_lazy as _

from sapl.crud import build_crud

from .models import (AssuntoNorma, LegislacaoCitada, NormaJuridica,
                     TipoNormaJuridica)

assunto_norma_crud = build_crud(
    AssuntoNorma,

    [_('Assunto Norma Jurídica'),
     [('assunto', 6), ('descricao', 6)]],
)

tipo_norma_crud = build_crud(
    TipoNormaJuridica,

    [_('Tipo Norma Jurídica'),
     [('descricao', 4),
      ('sigla', 4),
      ('equivalente_lexml', 4)]],
)

norma_crud = build_crud(
    NormaJuridica,

    [_('Identificação Básica'),
     [('tipo', 4), ('numero', 4), ('ano', 4)],
     [('data', 4), ('esfera_federacao', 4), ('complemento', 4)],
     [('tip_id_basica_FIXME', 4),
      ('num_ident_basica_FIXME', 4),
      ('ano_ident_basica_FIXME', 4)],
     [('data_publicacao', 3),
      ('veiculo_publicacao', 3),
      ('pagina_inicio_publicacao', 3),
      ('pagina_fim_publicacao', 3)],
     [('file_FIXME', 6), ('tip_situacao_norma_FIXME', 6)],
     [('ementa', 12)],
     [('indexacao', 12)],
     [('observacao', 12)]],

    [_('Assuntos (Classificação) [+] '),
     [('assunto_norma_FIXME', 12)],
     [('assunto_norma_FIXME', 12)],
     [('assunto_norma_FIXME', 12)]],
)

legislacao_citada_crud = build_crud(
    LegislacaoCitada,

    [_('Legislação Citada'),
     [('tip_norma_FIXME', 4),
      ('num_norma_FIXME', 4),
      ('ano_norma_FIXME', 4)],
     [('disposicoes', 3), ('parte', 3), ('livro', 3), ('titulo', 3)],
     [('capitulo', 3), ('secao', 3), ('subsecao', 3), ('artigo', 3)],
     [('paragrafo', 3), ('inciso', 3), ('alinea', 3), ('item', 3)]],
)
