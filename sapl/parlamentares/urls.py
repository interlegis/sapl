from django.conf.urls import include, url

from sapl.parlamentares.views import (CargoMesaCrud, ColigacaoCrud,
                                      ComposicaoColigacaoCrud, DependenteCrud,
                                      BancadaCrud, CargoBancadaCrud,
                                      FiliacaoCrud, FrenteCrud, FrenteList,
                                      LegislaturaCrud, MandatoCrud,
                                      MesaDiretoraView, NivelInstrucaoCrud,
                                      ParlamentarCrud, ParlamentarMateriasView,
                                      ParticipacaoParlamentarCrud, PartidoCrud,
                                      ProposicaoParlamentarCrud,
                                      RelatoriaParlamentarCrud,
                                      SessaoLegislativaCrud,
                                      TipoAfastamentoCrud, TipoDependenteCrud,
                                      AfastamentoParlamentarCrud,
                                      TipoMilitarCrud, VotanteView,
                                      altera_field_mesa,
                                      altera_field_mesa_public_view,
                                      frente_atualiza_lista_parlamentares,
                                      insere_parlamentar_composicao,
                                      parlamentares_frente_selected,
                                      remove_parlamentar_composicao,
                                      lista_parlamentares,
                                      parlamentares_filiados,
                                      BlocoCrud, CargoBlocoCrud,
                                      PesquisarParlamentarView, 
                                      VincularParlamentarView,
                                      deleta_historico_partido,
                                      edita_vinculo_parlamentar_bloco,
                                      deleta_vinculo_parlamentar_bloco,
                                      vincula_parlamentar_ao_bloco,
                                      get_sessoes_legislatura)


from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^parlamentar/', include(
        ParlamentarCrud.get_urls() + DependenteCrud.get_urls() +
        FiliacaoCrud.get_urls() + MandatoCrud.get_urls() +
        ParticipacaoParlamentarCrud.get_urls() +
        ProposicaoParlamentarCrud.get_urls() +
        RelatoriaParlamentarCrud.get_urls() + FrenteList.get_urls() +
        VotanteView.get_urls() + AfastamentoParlamentarCrud.get_urls()
    )),

    url(r'^parlamentar/lista$', lista_parlamentares, name='lista_parlamentares'),

    url(r'^parlamentar/pesquisar-parlamentar/',
        PesquisarParlamentarView.as_view(), name='pesquisar_parlamentar'),

    url(r'^parlamentar/deleta_partido/(?P<pk>\d+)/$',
        deleta_historico_partido, name='deleta_historico_partido'),

    url(r'^parlamentar/(?P<pk>\d+)/materias$',
        ParlamentarMateriasView.as_view(), name='parlamentar_materias'),

    url(r'^parlamentar/vincular-parlamentar/$',
        VincularParlamentarView.as_view(), name='vincular_parlamentar'),

    url(r'^sistema/coligacao/',
        include(ColigacaoCrud.get_urls() +
                ComposicaoColigacaoCrud.get_urls())),

    url(r'^sistema/bancada/',
        include(BancadaCrud.get_urls())),
    url(r'^sistema/cargo-bancada/',
        include(CargoBancadaCrud.get_urls())),

    url(r'^sistema/bloco/',
        include(BlocoCrud.get_urls())),
    url(r'^sistema/cargo-bloco/',
        include(CargoBlocoCrud.get_urls())),
    url(r'^sistema/vincula-parlamentar-ao-bloco/(?P<pk>\d+)/',
        vincula_parlamentar_ao_bloco,name='vincula_parlamentar_ao_bloco'),
    url(r'^sistema/edita-vinculo-parlamentar-bloco/(?P<pk>\d+)/',
        edita_vinculo_parlamentar_bloco,name='edita-vinculo-parlamentar-bloco'),
    url(r'^sistema/deleta-vinculo-parlamentar-bloco/(?P<pk>\d+)/',
        deleta_vinculo_parlamentar_bloco,name='deleta-vinculo-parlamentar-bloco'),
        
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
    url(r'^sistema/parlamentar/partido/(?P<pk>\d+)/filiados$', parlamentares_filiados, name='parlamentares_filiados'),

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

    url(r'^parlamentar/get-sessoes-legislatura/$',
        get_sessoes_legislatura, name='get_sessoes_legislatura'),

]
