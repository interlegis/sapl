from django.conf.urls import include, url

from parlamentares.views import (CargoMesaCrud, ColigacaoCrud,
                                 FiliacaoEditView, FiliacaoView,
                                 LegislaturaCrud, MandatoEditView, MandatoView,
                                 MesaDiretoraView, NivelInstrucaoCrud,
                                 ParlamentarCrud,
                                 ParlamentaresDependentesEditView,
                                 ParlamentaresDependentesView, PartidoCrud,
                                 SessaoLegislativaCrud, TipoAfastamentoCrud,
                                 TipoDependenteCrud, TipoMilitarCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^parlamentar/', include(ParlamentarCrud.get_urls())),

    url(r'^sistema/parlamentar/legislatura/',
        include(LegislaturaCrud.get_urls())),
    url(r'^sistema/parlamentar/tipo-dependente/',
        include(TipoDependenteCrud.get_urls())),
    url(r'^sistema/parlamentar/nivel-instrucao/',
        include(NivelInstrucaoCrud.get_urls())),
    url(r'^sistema/parlamentar/coligacao/',
        include(ColigacaoCrud.get_urls())),
    url(r'^sistema/parlamentar/tipo-afastamento/',
        include(TipoAfastamentoCrud.get_urls())),
    url(r'^sistema/parlamentar/tipo-militar/',
        include(TipoMilitarCrud.get_urls())),
    url(r'^sistema/parlamentar/partido/', include(PartidoCrud.get_urls())),

    url(r'^sistema/mesa-diretora/sessao-legislativa/',
        include(SessaoLegislativaCrud.get_urls())),
    url(r'^sistema/mesa-diretora/cargo-mesa/',
        include(CargoMesaCrud.get_urls())),

    url(r'^parlamentar/(?P<pk>\d+)/dependente$',
        ParlamentaresDependentesView.as_view(),
        name='parlamentar_dependente'),
    url(r'^parlamentar/(?P<pk>\d+)/dependente/(?P<dk>\d+)$',
        ParlamentaresDependentesEditView.as_view(),
        name='parlamentar_dependente_edit'),
    url(r'^parlamentar/(?P<pk>\d+)/filiacao$',
        FiliacaoView.as_view(),
        name='parlamentar_filiacao'),
    url(r'^parlamentar/(?P<pk>\d+)/filiacao/(?P<dk>\d+)$',
        FiliacaoEditView.as_view(),
        name='parlamentar_filiacao_edit'),
    url(r'^parlamentar/(?P<pk>\d+)/mandato$',
        MandatoView.as_view(),
        name='parlamentar_mandato'),
    url(r'^parlamentar/(?P<pk>\d+)/mandato/(?P<dk>\d+)$',
        MandatoEditView.as_view(),
        name='parlamentar_mandato_edit'),

    url(r'^mesa-diretora/$',
        MesaDiretoraView.as_view(), name='mesa_diretora'),
]
