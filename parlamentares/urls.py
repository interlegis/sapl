from django.conf.urls import include, url

from parlamentares.views import (CargoMesaCrud, ColigacaoCrud, DependenteCrud,
                                 FiliacaoEditView, FiliacaoView,
                                 LegislaturaCrud, MandatoCrud,
                                 MesaDiretoraView, NivelInstrucaoCrud,
                                 ParlamentarCrud, PartidoCrud,
                                 SessaoLegislativaCrud, TipoAfastamentoCrud,
                                 TipoDependenteCrud, TipoMilitarCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^parlamentar/', include(
        ParlamentarCrud.get_urls() + DependenteCrud.get_urls() +
        MandatoCrud.get_urls()
    )),

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

    url(r'^parlamentar/(?P<pk>\d+)/filiacao$',
        FiliacaoView.as_view(),
        name='parlamentar_filiacao'),
    url(r'^parlamentar/(?P<pk>\d+)/filiacao/(?P<dk>\d+)$',
        FiliacaoEditView.as_view(),
        name='parlamentar_filiacao_edit'),

    url(r'^mesa-diretora/$',
        MesaDiretoraView.as_view(), name='mesa_diretora'),
]
