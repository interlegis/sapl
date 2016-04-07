from django.conf.urls import include, url

from comissoes.views import (CargoCrud, ComissaoCrud,
                             ComissaoParlamentarEditView,
                             ComissaoParlamentarIncluirView, ComposicaoView,
                             MateriasTramitacaoListView, PeriodoComposicaoCrud,
                             TipoComissaoCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^comissoes/', include(ComissaoCrud.get_urls())),

    url(r'^comissoes/(?P<pk>\d+)/composicao$',
        ComposicaoView.as_view(), name='composicao'),
    url(r'^comissoes/(?P<pk>\d+)/materias-em-tramitacao$',
        MateriasTramitacaoListView.as_view(), name='materias_em_tramitacao'),

    url(r'^comissoes/(?P<pk>\d+)/composicao/(?P<id>\d+)/parlamentar$',
        ComissaoParlamentarIncluirView.as_view(),
        name='comissao_parlamentar'),
    url(r'''^comissoes/(?P<pk>\d+)/composicao/(?P<cd>\d+)/
        parlamentar/(?P<id>\d+)/edit$''',
        ComissaoParlamentarEditView.as_view(),
        name='comissao_parlamentar_edit'),

    url(r'^sistema/comissoes/cargo/', include(CargoCrud.get_urls())),
    url(r'^sistema/comissoes/periodo-composicao/',
        include(PeriodoComposicaoCrud.get_urls())),
    url(r'^sistema/comissoes/tipo/', include(TipoComissaoCrud.get_urls())),
]
