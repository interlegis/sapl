from django.conf.urls import include, url

from sapl.parlamentares.views import (CargoMesaCrud, ColigacaoCrud,
                                      ComposicaoColigacaoCrud, DependenteCrud,
                                      FiliacaoCrud, FrenteCrud, FrenteList,
                                      LegislaturaCrud, MandatoCrud,
                                      MesaDiretoraView, NivelInstrucaoCrud,
                                      ParlamentarCrud, ParlamentarMateriasView,
                                      ParticipacaoParlamentarCrud, PartidoCrud,
                                      ProposicaoParlamentarCrud,
                                      RelatoriaParlamentarCrud,
                                      SessaoLegislativaCrud,
                                      TipoAfastamentoCrud, TipoDependenteCrud,
                                      TipoMilitarCrud, VotanteView,
                                      altera_field_mesa,
                                      altera_field_mesa_public_view,
                                      frente_atualiza_lista_parlamentares,
                                      insere_parlamentar_composicao,
                                      parlamentares_frente_selected,
                                      remove_parlamentar_composicao)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^parlamentar/', include(
        ParlamentarCrud.get_urls() + DependenteCrud.get_urls() +
        FiliacaoCrud.get_urls() + MandatoCrud.get_urls() +
        ParticipacaoParlamentarCrud.get_urls() +
        ProposicaoParlamentarCrud.get_urls() +
        RelatoriaParlamentarCrud.get_urls() + FrenteList.get_urls() +
        VotanteView.get_urls()
    )),

    url(r'^parlamentar/(?P<pk>\d+)/materias$',
        ParlamentarMateriasView.as_view(), name='parlamentar_materias'),

    url(r'^sistema/coligacao/',
        include(ColigacaoCrud.get_urls() +
                ComposicaoColigacaoCrud.get_urls())),

    url(r'^sistema/frente/',
        include(FrenteCrud.get_urls())),
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

    url(r'^sistema/mesa-diretora/sessao-legislativa/',
        include(SessaoLegislativaCrud.get_urls())),
    url(r'^sistema/mesa-diretora/cargo-mesa/',
        include(CargoMesaCrud.get_urls())),

    url(r'^mesa-diretora/$',
        MesaDiretoraView.as_view(), name='mesa_diretora'),

    url(r'^mesa-diretora/altera-field-mesa/$',
        altera_field_mesa, name='altera_field_mesa'),

    url(r'^mesa-diretora/altera-field-mesa-public-view/$',
        altera_field_mesa_public_view, name='altera_field_mesa_public_view'),

    url(r'^mesa-diretora/insere-parlamentar-composicao/$',
        insere_parlamentar_composicao, name='insere_parlamentar_composicao'),

    url(r'^mesa-diretora/remove-parlamentar-composicao/$',
        remove_parlamentar_composicao, name='remove_parlamentar_composicao'),
]
