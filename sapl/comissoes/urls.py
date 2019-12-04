from django.conf.urls import include, url
from sapl.comissoes.views import (AdicionaPautaView, CargosComissaoOrdenacaoView, CargoCrud,
                                  ComissaoCrud, ComposicaoCrud, DocumentoAcessorioCrud,
                                  MateriasTramitacaoListView, ParticipacaoCrud,
                                  get_participacoes_comissao, PeriodoComposicaoCrud,
                                  RemovePautaView, ReuniaoCrud, TipoComissaoCrud)

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

    url(r'^comissao/(?P<pk>\d+)/pauta/add', AdicionaPautaView.as_view(), name='pauta_add'),
    url(r'^comissao/(?P<pk>\d+)/pauta/remove', RemovePautaView.as_view(), name='pauta_remove'),

    url(r'^sistema/comissao/cargo/', include(CargoCrud.get_urls())),
    url(r'^sistema/comissao/cargos-ordenacao',
        CargosComissaoOrdenacaoView.as_view(), name='cargos_comissao_ordenacao'),
    url(r'^sistema/comissao/periodo-composicao/',
        include(PeriodoComposicaoCrud.get_urls())),
    url(r'^sistema/comissao/tipo/', include(TipoComissaoCrud.get_urls())),
    url(r'^sistema/comissao/recupera-participacoes', get_participacoes_comissao),
]
