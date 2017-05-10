from django.conf.urls import include, url

from sapl.parlamentares.views import (altera_field_mesa,
                                      CargoMesaCrud, ColigacaoCrud,
                                      ComposicaoColigacaoCrud, DependenteCrud,
                                      FiliacaoCrud, FrenteCrud, FrenteList,
                                      LegislaturaCrud,
                                      insere_parlamentar_composicao,
                                      MandatoCrud,
                                      MesaDiretoraView, NivelInstrucaoCrud,
                                      ParlamentarCrud,
                                      ParticipacaoParlamentarCrud, PartidoCrud,
                                      ProposicaoParlamentarCrud,
                                      RelatoriaParlamentarCrud,
                                      remove_parlamentar_composicao,
                                      SessaoLegislativaCrud,
                                      TipoAfastamentoCrud, TipoDependenteCrud,
                                      TipoMilitarCrud, VotanteView)

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

    url(r'^sistema/coligacao/',
        include(ColigacaoCrud.get_urls() +
                ComposicaoColigacaoCrud.get_urls())),
    url(r'^sistema/frente/',
        include(FrenteCrud.get_urls())),
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

    url(r'^mesa-diretora/insere-parlamentar-composicao/$',
        insere_parlamentar_composicao, name='insere_parlamentar_composicao'),

    url(r'^mesa-diretora/remove-parlamentar-composicao/$',
        remove_parlamentar_composicao, name='remove_parlamentar_composicao'),
]
