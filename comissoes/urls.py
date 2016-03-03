"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from django.conf.urls import include, url

from comissoes.views import (CadastrarComissaoView,
                             ComissaoParlamentarEditView,
                             ComissaoParlamentarIncluirView, ComposicaoView,
                             MateriasTramitacaoListView, MateriasView,
                             ReunioesView, cargo_crud, comissao_crud,
                             periodo_composicao_crud, tipo_comissao_crud)

comissao_url_patterns = comissao_crud.urlpatterns + [
    url(r'^(?P<pk>\d+)/composicao$',
        ComposicaoView.as_view(), name='composicao'),
    url(r'^(?P<pk>\d+)/materias-em-tramitacao$',
        MateriasTramitacaoListView.as_view(), name='materias_em_tramitacao'),
    url(r'^(?P<pk>\d+)/composicao/(?P<id>\d+)/parlamentar$',
        ComissaoParlamentarIncluirView.as_view(),
        name='comissao_parlamentar'),
    url(r'^(?P<pk>\d+)/composicao/(?P<cd>\d+)/parlamentar/(?P<id>\d+)/edit$',
        ComissaoParlamentarEditView.as_view(),
        name='comissao_parlamentar_edit'),
    url(r'^(?P<pk>\d+)/materias$',
        MateriasView.as_view(), name='materias'),
    url(r'^(?P<pk>\d+)/reunioes$',
        ReunioesView.as_view(), name='reunioes'),
    url(r'^cadastrar-comissao$',
        CadastrarComissaoView.as_view(), name='cadastrar_comissao'),
]

urlpatterns = [
    url(r'^comissoes/', include(comissao_url_patterns,
                                comissao_crud.namespace,
                                comissao_crud.namespace)),

    url(r'^sistema/comissoes/cargo/', include(cargo_crud.urls)),
    url(r'^sistema/comissoes/periodo-composicao/',
        include(periodo_composicao_crud.urls)),
    url(r'^sistema/comissoes/tipo/', include(tipo_comissao_crud.urls)),
]
