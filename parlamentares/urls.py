from django.conf.urls import include, url

from parlamentares.views import (CargoMesaCrud, ColigacaoCrud,
                                 FiliacaoEditView, FiliacaoView,
                                 LegislaturaCrud, MandatoEditView, MandatoView,
                                 MesaDiretoraView, NivelInstrucaoCrud,
                                 ParlamentaresCadastroView,
                                 ParlamentaresDependentesEditView,
                                 ParlamentaresDependentesView,
                                 ParlamentaresEditarView, ParlamentaresView,
                                 PartidoCrud, SessaoLegislativaCrud,
                                 TipoAfastamentoCrud, TipoDependenteCrud,
                                 TipoMilitarCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^sistema/parlamentares/legislatura/',
        include(LegislaturaCrud.get_urls())),
    url(r'^sistema/parlamentares/tipo-dependente/',
        include(TipoDependenteCrud.get_urls())),
    url(r'^sistema/parlamentares/nivel-instrucao/',
        include(NivelInstrucaoCrud.get_urls())),
    url(r'^sistema/parlamentares/coligacao/',
        include(ColigacaoCrud.get_urls())),
    url(r'^sistema/parlamentares/tipo-afastamento/',
        include(TipoAfastamentoCrud.get_urls())),
    url(r'^sistema/parlamentares/tipo-militar/',
        include(TipoMilitarCrud.get_urls())),
    url(r'^sistema/parlamentares/partido/', include(PartidoCrud.get_urls())),

    url(r'^sistema/mesa-diretora/sessao-legislativa/',
        include(SessaoLegislativaCrud.get_urls())),
    url(r'^sistema/mesa-diretora/cargo-mesa/',
        include(CargoMesaCrud.get_urls())),

    url(r'^parlamentares/$',
        ParlamentaresView.as_view(), name='parlamentares'),
    url(r'^parlamentares/(?P<pk>\d+)/cadastro$',
        ParlamentaresCadastroView.as_view(), name='parlamentares_cadastro'),
    url(r'^parlamentares/(?P<pk>\d+)/dependentes$',
        ParlamentaresDependentesView.as_view(),
        name='parlamentares_dependentes'),
    url(r'^parlamentares/(?P<pk>\d+)/dependentes/(?P<dk>\d+)$',
        ParlamentaresDependentesEditView.as_view(),
        name='parlamentares_dependentes_edit'),
    url(r'^parlamentares/(?P<pk>\d+)/filiacao$',
        FiliacaoView.as_view(),
        name='parlamentares_filiacao'),
    url(r'^parlamentares/(?P<pk>\d+)/filiacao/(?P<dk>\d+)$',
        FiliacaoEditView.as_view(),
        name='parlamentares_filiacao_edit'),
    url(r'^parlamentares/(?P<pk>\d+)/mandato$',
        MandatoView.as_view(),
        name='parlamentares_mandato'),
    url(r'^parlamentares/(?P<pk>\d+)/mandato/(?P<dk>\d+)$',
        MandatoEditView.as_view(),
        name='parlamentares_mandato_edit'),

    url(r'^parlamentares/(?P<pk>\d+)/editar$',
        ParlamentaresEditarView.as_view(), name='parlamentares_editar'),

    url(r'^mesa-diretora/$',
        MesaDiretoraView.as_view(), name='mesa_diretora'),
]
