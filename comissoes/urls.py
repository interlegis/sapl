from django.conf.urls import include, url

from comissoes.views import (CargoCrud, ComissaoCrud,
                             ComissaoParlamentarEditView,
                             ComissaoParlamentarIncluirView, ComposicaoCrud,
                             MateriasTramitacaoListView, PeriodoComposicaoCrud,
                             TipoComissaoCrud, ParticipacaoCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^comissao/', include(ComissaoCrud.get_urls() +
                               ComposicaoCrud.get_urls() +
                               ParticipacaoCrud.get_urls())),

    url(r'^comissao/(?P<pk>\d+)/materias-em-tramitacao$',
        MateriasTramitacaoListView.as_view(), name='materias_em_tramitacao'),

    url(r'^comissao/(?P<pk>\d+)/composicao/(?P<id>\d+)/parlamentar$',
        ComissaoParlamentarIncluirView.as_view(),
        name='comissao_parlamentar'),
    url(r'''^comissao/(?P<pk>\d+)/composicao/(?P<cd>\d+)/
        parlamentar/(?P<id>\d+)/edit$''',
        ComissaoParlamentarEditView.as_view(),
        name='comissao_parlamentar_edit'),

    url(r'^sistema/comissao/cargo/', include(CargoCrud.get_urls())),
    url(r'^sistema/comissao/periodo-composicao/',
        include(PeriodoComposicaoCrud.get_urls())),
    url(r'^sistema/comissao/tipo/', include(TipoComissaoCrud.get_urls())),
]
