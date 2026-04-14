from django.conf.urls import include, url

from sapl.parlamentares.views import (CargoMesaCrud, ColigacaoCrud, ComposicaoMesaCrud, MesaDiretoraCrud,
                                      coligacao_legislatura,
                                      ComposicaoColigacaoCrud, DependenteCrud,
                                      FiliacaoCrud, FrenteCrud, FrenteList,
                                      LegislaturaCrud, MandatoCrud,
                                      NivelInstrucaoCrud,
                                      ParlamentarCrud, ParlamentarMateriasView, ParlamentarNormasView,
                                      ParticipacaoParlamentarCrud, PartidoCrud,
                                      ProposicaoParlamentarCrud,
                                      RelatoriaParlamentarCrud,
                                      SessaoLegislativaCrud,
                                      TipoAfastamentoCrud, TipoDependenteCrud,
                                      TipoMilitarCrud, VotanteView,
                                      frente_atualiza_lista_parlamentares,
                                      parlamentares_frente_selected,
                                      parlamentares_filiados, BlocoCrud,
                                      PesquisarParlamentarView, VincularParlamentarView,
                                      get_sessoes_legislatura, FrenteCargoCrud, FrenteParlamentarCrud,
                                      get_parlamentar_frentes, PesquisarColigacaoView, PesquisarPartidoView,
                                      BlocoCargoCrud, BlocoMembroCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^parlamentar/', include(
        ParlamentarCrud.get_urls() + DependenteCrud.get_urls() +
        FiliacaoCrud.get_urls() + MandatoCrud.get_urls() +
        ParticipacaoParlamentarCrud.get_urls() +
        ProposicaoParlamentarCrud.get_urls() +
        RelatoriaParlamentarCrud.get_urls() +
        VotanteView.get_urls()


    )),

    url(r'^parlamentar/pesquisar-parlamentar/',
        PesquisarParlamentarView.as_view(), name='pesquisar_parlamentar'),

    url(r'^parlamentar/(?P<pk>\d+)/materias$',
        ParlamentarMateriasView.as_view(), name='parlamentar_materias'),

    url(r'^parlamentar/(?P<pk>\d+)/normas$',
        ParlamentarNormasView.as_view(), name='parlamentar_normas'),

    url(r'^parlamentar/(?P<pk>\d+)/frentes/$',
        get_parlamentar_frentes, name='parlamentar_frentes'),

    url(r'^parlamentar/vincular-parlamentar/$',
        VincularParlamentarView.as_view(), name='vincular_parlamentar'),

    url(r'^parlamentar/coligacao-legislatura/',
        coligacao_legislatura, name="coligacao_legislatura"),
    url(r'^sistema/coligacao/', include(ColigacaoCrud.get_urls() +
                                        ComposicaoColigacaoCrud.get_urls())),
    url(r'^sistema/pesquisar-coligacao/',
        PesquisarColigacaoView.as_view(), name='pesquisar_coligacao'),

    url(r'^sistema/coligacao/', include(ColigacaoCrud.get_urls() +
                                        ComposicaoColigacaoCrud.get_urls())),

    url(r'^sistema/bloco/', include(BlocoCrud.get_urls())),
    url(r'^sistema/bloco-cargo/', include(BlocoCargoCrud.get_urls())),
    url(r'^sistema/bloco-membros/', include(BlocoMembroCrud.get_urls())),

    url(r'^sistema/frente/', include(FrenteCrud.get_urls())),
    url(r'^sistema/frente-cargo/', include(FrenteCargoCrud.get_urls())),
    url(r'^sistema/frente-parlamentares/',
        include(FrenteParlamentarCrud.get_urls())),

    url(r'^sistema/frente/atualiza-lista-parlamentares',
        frente_atualiza_lista_parlamentares,
        name='atualiza_lista_parlamentares'),
    url(r'^sistema/frente/parlamentares-frente-selected',
        parlamentares_frente_selected,
        name='parlamentares_frente_selected'),

    url(r'^sistema/parlamentar/legislatura/',
        include(LegislaturaCrud.get_urls())),
    url(r'^sistema/parlamentar/tipo-dependente/',
        include(TipoDependenteCrud.get_urls())),
    url(r'^sistema/parlamentar/nivel-instrucao/',
        include(NivelInstrucaoCrud.get_urls())),
    url(r'^sistema/parlamentar/tipo-afastamento/',
        include(TipoAfastamentoCrud.get_urls())),
    url(r'^sistema/parlamentar/tipo-militar/',
        include(TipoMilitarCrud.get_urls())),

    url(r'^sistema/parlamentar/partido/', include(PartidoCrud.get_urls())),
    url(r'^sistema/parlamentar/pesquisar-partido/',
        PesquisarPartidoView.as_view(), name='pesquisar_partido'),
    url(r'^sistema/parlamentar/partido/(?P<pk>\d+)/filiados$',
        parlamentares_filiados, name='parlamentares_filiados'),

    url(r'^sistema/mesa-diretora/sessao-legislativa/',
        include(SessaoLegislativaCrud.get_urls())),
    url(r'^sistema/mesa-diretora/cargo-mesa/',
        include(CargoMesaCrud.get_urls())),

    url(r'^mesa-diretora/', include(
        MesaDiretoraCrud.get_urls() +
        ComposicaoMesaCrud.get_urls()
    )),

    url(r'^parlamentar/get-sessoes-legislatura/$',
        get_sessoes_legislatura, name='get_sessoes_legislatura'),
]
