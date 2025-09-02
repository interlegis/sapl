from django.urls import include, path, re_path

from sapl.parlamentares.views import (BlocoCargoCrud, BlocoCrud,
                                      BlocoMembroCrud, CargoMesaCrud,
                                      ColigacaoCrud, ComposicaoColigacaoCrud,
                                      DependenteCrud, FiliacaoCrud,
                                      FrenteCargoCrud, FrenteCrud, FrenteList,
                                      FrenteParlamentarCrud, LegislaturaCrud,
                                      MandatoCrud, MesaDiretoraView,
                                      NivelInstrucaoCrud, ParlamentarCrud,
                                      ParlamentarMateriasView,
                                      ParlamentarNormasView,
                                      ParticipacaoParlamentarCrud, PartidoCrud,
                                      PesquisarColigacaoView,
                                      PesquisarParlamentarView,
                                      PesquisarPartidoView,
                                      ProposicaoParlamentarCrud,
                                      RelatoriaParlamentarCrud,
                                      SessaoLegislativaCrud,
                                      TipoAfastamentoCrud, TipoDependenteCrud,
                                      TipoMilitarCrud, VincularParlamentarView,
                                      VotanteView, altera_field_mesa,
                                      altera_field_mesa_public_view,
                                      coligacao_legislatura,
                                      frente_atualiza_lista_parlamentares,
                                      get_parlamentar_frentes,
                                      get_sessoes_legislatura,
                                      insere_parlamentar_composicao,
                                      parlamentares_filiados,
                                      parlamentares_frente_selected,
                                      remove_parlamentar_composicao)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    path(
        "parlamentar/",
        include(
            ParlamentarCrud.get_urls()
            + DependenteCrud.get_urls()
            + FiliacaoCrud.get_urls()
            + MandatoCrud.get_urls()
            + ParticipacaoParlamentarCrud.get_urls()
            + ProposicaoParlamentarCrud.get_urls()
            + RelatoriaParlamentarCrud.get_urls()
            + VotanteView.get_urls()
        ),
    ),
    re_path(
        r"^parlamentar/pesquisar-parlamentar/",
        PesquisarParlamentarView.as_view(),
        name="pesquisar_parlamentar",
    ),
    path(
        "parlamentar/<int:pk>/materias",
        ParlamentarMateriasView.as_view(),
        name="parlamentar_materias",
    ),
    path(
        "parlamentar/<int:pk>/normas",
        ParlamentarNormasView.as_view(),
        name="parlamentar_normas",
    ),
    path(
        "parlamentar/<int:pk>/frentes/",
        get_parlamentar_frentes,
        name="parlamentar_frentes",
    ),
    path(
        "parlamentar/vincular-parlamentar/",
        VincularParlamentarView.as_view(),
        name="vincular_parlamentar",
    ),
    re_path(
        r"^parlamentar/coligacao-legislatura/",
        coligacao_legislatura,
        name="coligacao_legislatura",
    ),
    path(
        "sistema/coligacao/",
        include(ColigacaoCrud.get_urls() + ComposicaoColigacaoCrud.get_urls()),
    ),
    re_path(
        r"^sistema/pesquisar-coligacao/",
        PesquisarColigacaoView.as_view(),
        name="pesquisar_coligacao",
    ),
    path(
        "sistema/coligacao/",
        include(ColigacaoCrud.get_urls() + ComposicaoColigacaoCrud.get_urls()),
    ),
    path("sistema/bloco/", include(BlocoCrud.get_urls())),
    path("sistema/bloco-cargo/", include(BlocoCargoCrud.get_urls())),
    path("sistema/bloco-membros/", include(BlocoMembroCrud.get_urls())),
    path("sistema/frente/", include(FrenteCrud.get_urls())),
    path("sistema/frente-cargo/", include(FrenteCargoCrud.get_urls())),
    path("sistema/frente-parlamentares/", include(FrenteParlamentarCrud.get_urls())),
    re_path(
        r"^sistema/frente/atualiza-lista-parlamentares",
        frente_atualiza_lista_parlamentares,
        name="atualiza_lista_parlamentares",
    ),
    re_path(
        r"^sistema/frente/parlamentares-frente-selected",
        parlamentares_frente_selected,
        name="parlamentares_frente_selected",
    ),
    path("sistema/parlamentar/legislatura/", include(LegislaturaCrud.get_urls())),
    path(
        "sistema/parlamentar/tipo-dependente/", include(TipoDependenteCrud.get_urls())
    ),
    path(
        "sistema/parlamentar/nivel-instrucao/", include(NivelInstrucaoCrud.get_urls())
    ),
    path(
        "sistema/parlamentar/tipo-afastamento/", include(TipoAfastamentoCrud.get_urls())
    ),
    path("sistema/parlamentar/tipo-militar/", include(TipoMilitarCrud.get_urls())),
    path("sistema/parlamentar/partido/", include(PartidoCrud.get_urls())),
    re_path(
        r"^sistema/parlamentar/pesquisar-partido/",
        PesquisarPartidoView.as_view(),
        name="pesquisar_partido",
    ),
    path(
        "sistema/parlamentar/partido/<int:pk>/filiados",
        parlamentares_filiados,
        name="parlamentares_filiados",
    ),
    path(
        "sistema/mesa-diretora/sessao-legislativa/",
        include(SessaoLegislativaCrud.get_urls()),
    ),
    path("sistema/mesa-diretora/cargo-mesa/", include(CargoMesaCrud.get_urls())),
    path("mesa-diretora/", MesaDiretoraView.as_view(), name="mesa_diretora"),
    path(
        "mesa-diretora/altera-field-mesa/", altera_field_mesa, name="altera_field_mesa"
    ),
    path(
        "mesa-diretora/altera-field-mesa-public-view/",
        altera_field_mesa_public_view,
        name="altera_field_mesa_public_view",
    ),
    path(
        "mesa-diretora/insere-parlamentar-composicao/",
        insere_parlamentar_composicao,
        name="insere_parlamentar_composicao",
    ),
    path(
        "mesa-diretora/remove-parlamentar-composicao/",
        remove_parlamentar_composicao,
        name="remove_parlamentar_composicao",
    ),
    path(
        "parlamentar/get-sessoes-legislatura/",
        get_sessoes_legislatura,
        name="get_sessoes_legislatura",
    ),
]
