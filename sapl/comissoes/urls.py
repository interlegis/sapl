from django.urls.conf import path, include
from sapl.comissoes.views import (AdicionaPautaView, CargoComissaoCrud, ComissaoCrud,
                                  ComposicaoCrud, DocumentoAcessorioCrud,
                                  MateriasTramitacaoListView, ParticipacaoCrud,
                                  get_participacoes_comissao, PeriodoComposicaoCrud,
                                  RemovePautaView, ReuniaoCrud, TipoComissaoCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    path(r'^comissao/', include(ComissaoCrud.get_urls() +
                               ComposicaoCrud.get_urls() +
                               ReuniaoCrud.get_urls() +
                               ParticipacaoCrud.get_urls() +
                               DocumentoAcessorioCrud.get_urls())),

    path(r'^comissao/(?P<pk>\d+)/materias-em-tramitacao$',
        MateriasTramitacaoListView.as_view(), name='materias_em_tramitacao'),

    path(r'^comissao/(?P<pk>\d+)/pauta/add', AdicionaPautaView.as_view(), name='pauta_add'),
    path(r'^comissao/(?P<pk>\d+)/pauta/remove', RemovePautaView.as_view(), name='pauta_remove'),

    path(r'^sistema/comissao/cargo/', include(CargoComissaoCrud.get_urls())),
    path(r'^sistema/comissao/periodo-composicao/',
        include(PeriodoComposicaoCrud.get_urls())),
    path(r'^sistema/comissao/tipo/', include(TipoComissaoCrud.get_urls())),
    path(r'^sistema/comissao/recupera-participacoes', get_participacoes_comissao),
]
