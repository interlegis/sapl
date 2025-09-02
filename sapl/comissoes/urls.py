from django.urls import include, path, re_path

from sapl.comissoes.views import (AdicionaPautaView, CargoComissaoCrud,
                                  ComissaoCrud, ComposicaoCrud,
                                  DocumentoAcessorioCrud,
                                  MateriasTramitacaoListView, ParticipacaoCrud,
                                  PeriodoComposicaoCrud, RemovePautaView,
                                  ReuniaoCrud, TipoComissaoCrud,
                                  get_participacoes_comissao)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    path(
        "comissao/",
        include(
            ComissaoCrud.get_urls()
            + ComposicaoCrud.get_urls()
            + ReuniaoCrud.get_urls()
            + ParticipacaoCrud.get_urls()
            + DocumentoAcessorioCrud.get_urls()
        ),
    ),
    path(
        "comissao/<int:pk>/materias-em-tramitacao",
        MateriasTramitacaoListView.as_view(),
        name="materias_em_tramitacao",
    ),
    re_path(
        r"^comissao/(?P<pk>\d+)/pauta/add",
        AdicionaPautaView.as_view(),
        name="pauta_add",
    ),
    re_path(
        r"^comissao/(?P<pk>\d+)/pauta/remove",
        RemovePautaView.as_view(),
        name="pauta_remove",
    ),
    path("sistema/comissao/cargo/", include(CargoComissaoCrud.get_urls())),
    path(
        "sistema/comissao/periodo-composicao/",
        include(PeriodoComposicaoCrud.get_urls()),
    ),
    path("sistema/comissao/tipo/", include(TipoComissaoCrud.get_urls())),
    re_path(r"^sistema/comissao/recupera-participacoes", get_participacoes_comissao),
]
