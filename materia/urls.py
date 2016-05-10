from django.conf.urls import include, url

from materia.views import (AcompanhamentoConfirmarView,
                           AcompanhamentoExcluirView,
                           AcompanhamentoMateriaView, AnexadaCrud, AutorCrud,
                           AutoriaCrud, DespachoInicialCrud,
                           DocumentoAcessorioCrud, LegislacaoCitadaCrud,
                           MateriaLegislativaCrud,
                           MateriaLegislativaPesquisaView, MateriaTaView,
                           NumeracaoCrud, OrgaoCrud, OrigemCrud,
                           ProposicaoEditView, ProposicaoListView,
                           ProposicaoTaView, ProposicaoView,
                           RegimeTramitacaoCrud, RelatoriaCrud,
                           StatusTramitacaoCrud, TipoAutorCrud,
                           TipoDocumentoCrud, TipoFimRelatoriaCrud,
                           TipoMateriaCrud, TipoProposicaoCrud, TramitacaoCrud,
                           UnidadeTramitacaoCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^materia/', include(MateriaLegislativaCrud.get_urls() +
                              AnexadaCrud.get_urls() +
                              AutoriaCrud.get_urls() +
                              DespachoInicialCrud.get_urls() +
                              NumeracaoCrud.get_urls() +
                              LegislacaoCitadaCrud.get_urls() +
                              TramitacaoCrud.get_urls() +
                              RelatoriaCrud.get_urls() +
                              DocumentoAcessorioCrud.get_urls())),

    # Integração com Compilação
    url(r'^materia/(?P<pk>[0-9]+)/ta$',
        MateriaTaView.as_view(), name='materia_ta'),
    url(r'^materia/proposicao/(?P<pk>[0-9]+)/ta$',
        ProposicaoTaView.as_view(), name='proposicao_ta'),

    url(r'^sistema/proposicao/tipo/',
        include(TipoProposicaoCrud.get_urls())),
    url(r'^sistema/proposicao/autor/', include(AutorCrud.get_urls())),
    url(r'^sistema/materia/tipo/', include(TipoMateriaCrud.get_urls())),
    url(r'^sistema/materia/regime-tramitacao/',
        include(RegimeTramitacaoCrud.get_urls())),
    url(r'^sistema/materia/tipo-autor/', include(TipoAutorCrud.get_urls())),
    url(r'^sistema/materia/tipo-documento/',
        include(TipoDocumentoCrud.get_urls())),
    url(r'^sistema/materia/tipo-fim-relatoria/',
        include(TipoFimRelatoriaCrud.get_urls())),
    url(r'^sistema/materia/unidade-tramitacao/',
        include(UnidadeTramitacaoCrud.get_urls())),
    url(r'^sistema/materia/origem/', include(OrigemCrud.get_urls())),
    url(r'^sistema/materia/autor/', include(AutorCrud.get_urls())),
    url(r'^sistema/materia/status-tramitacao/',
        include(StatusTramitacaoCrud.get_urls())),
    url(r'^sistema/materia/orgao/', include(OrgaoCrud.get_urls())),
    url(r'^materia/proposicao$',
        ProposicaoView.as_view(), name='adicionar_proposicao'),
    url(r'^materia/proposicao_list$',
        ProposicaoListView.as_view(), name='list_proposicao'),
    url(r'^materia/proposicao/(?P<pk>[0-9]+)/edit$',
        ProposicaoEditView.as_view(), name='editar_proposicao'),
    url(r'^materia/pesquisar-materia$',
        MateriaLegislativaPesquisaView.as_view(), name='pesquisar_materia'),
    url(r'^materia/(?P<pk>\d+)/acompanhar-materia/$',
        AcompanhamentoMateriaView.as_view(), name='acompanhar_materia'),
    url(r'^materia/(?P<pk>\d+)/acompanhar-confirmar$',
        AcompanhamentoConfirmarView.as_view(),
        name='acompanhar_confirmar'),
    url(r'^materia/(?P<pk>\d+)/acompanhar-excluir$',
        AcompanhamentoExcluirView.as_view(),
        name='acompanhar_excluir'),
]
