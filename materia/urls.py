from django.conf.urls import include, url

from materia.views import (AcompanhamentoConfirmarView,
                           AcompanhamentoExcluirView,
                           AcompanhamentoMateriaView, AnexadaCrud, AutorCrud,
                           AutoriaCrud, DespachoInicialCrud,
                           DocumentoAcessorioEditView, DocumentoAcessorioView,
                           LegislacaoCitadaEditView, LegislacaoCitadaView,
                           MateriaLegislativaCrud,
                           MateriaLegislativaPesquisaView, MateriaTaView,
                           NumeracaoCrud, OrgaoCrud, OrigemCrud,
                           ProposicaoEditView, ProposicaoListView,
                           ProposicaoTaView, ProposicaoView,
                           RegimeTramitacaoCrud, RelatoriaEditView,
                           RelatoriaView, StatusTramitacaoCrud, TipoAutorCrud,
                           TipoDocumentoCrud, TipoFimRelatoriaCrud,
                           TipoMateriaCrud, TipoProposicaoCrud,
                           TramitacaoEditView, TramitacaoView,
                           UnidadeTramitacaoCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^materia/', include(MateriaLegislativaCrud.get_urls() +
                              AnexadaCrud.get_urls() +
                              AutoriaCrud.get_urls() +
                              DespachoInicialCrud.get_urls() +
                              NumeracaoCrud.get_urls())),


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
    url(r'^materia/(?P<pk>\d+)/legislacao-citada$',
        LegislacaoCitadaView.as_view(), name='legislacao_citada'),
    url(r'^materia/(?P<pk>\d+)/legislacao-citada/(?P<id>\d+)/edit',
        LegislacaoCitadaEditView.as_view(), name='legislacao_citada_edit'),
    url(r'^materia/(?P<pk>\d+)/documento-acessorio$',
        DocumentoAcessorioView.as_view(), name='documento_acessorio'),
    url(r'^materia/(?P<pk>\d+)/documento-acessorio/(?P<id>\d+)/edit',
        DocumentoAcessorioEditView.as_view(), name='documento_acessorio_edit'),
    url(r'^materia/(?P<pk>\d+)/relatoria$',
        RelatoriaView.as_view(), name='relatoria'),
    url(r'^materia/(?P<pk>\d+)/tramitacao$',
        TramitacaoView.as_view(), name='tramitacao_materia'),
    url(r'^materia/(?P<pk>\d+)/tramitacao/(?P<id>\d+)/edit$',
        TramitacaoEditView.as_view(), name='tramitacao_edit'),
    url(r'^materia/(?P<pk>\d+)/relatoria/(?P<id>\d+)/edit$',
        RelatoriaEditView.as_view(), name='relatoria_edit'),
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
