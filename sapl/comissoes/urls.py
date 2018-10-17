from django.conf.urls import include, url
from sapl.comissoes.views import (CargoCrud, ComissaoCrud, ComposicaoCrud,
                                  DocumentoAcessorioCrud, MateriasTramitacaoListView, ParticipacaoCrud,
                                  PeriodoComposicaoCrud, ReuniaoCrud, TipoComissaoCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^comissao/', include(ComissaoCrud.get_urls() +
                               ComposicaoCrud.get_urls() +
                               ReuniaoCrud.get_urls() +
                               ParticipacaoCrud.get_urls() +
                               DocumentoAcessorioCrud.get_urls())),

    url(r'^comissao/(?P<pk>\d+)/materias-em-tramitacao$',
        MateriasTramitacaoListView.as_view(), name='materias_em_tramitacao'),

    url(r'^sistema/comissao/cargo/', include(CargoCrud.get_urls())),
    url(r'^sistema/comissao/periodo-composicao/',
        include(PeriodoComposicaoCrud.get_urls())),
    url(r'^sistema/comissao/tipo/', include(TipoComissaoCrud.get_urls())),
]
