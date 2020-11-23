from django.conf.urls import include, url

from sapl.materia.views import (AcompanhamentoConfirmarView,
                                AcompanhamentoExcluirView,
                                AcompanhamentoMateriaView, AnexadaCrud,
                                AssuntoMateriaCrud, AutoriaCrud,
                                AutoriaMultiCreateView, ConfirmarProposicao,
                                CriarProtocoloMateriaView, DespachoInicialCrud,
                                DocumentoAcessorioCrud,
                                DocumentoAcessorioEmLoteView,
                                MateriaAnexadaEmLoteView,
                                EtiquetaPesquisaView, FichaPesquisaView,
                                FichaSelecionaView, ImpressosView,
                                LegislacaoCitadaCrud, MateriaAssuntoCrud,
                                MateriaLegislativaCrud,
                                MateriaLegislativaPesquisaView, MateriaTaView,
                                NumeracaoCrud, OrgaoCrud, OrigemCrud,
                                PrimeiraTramitacaoEmLoteView, ProposicaoCrud,
                                ProposicaoDevolvida, ProposicaoPendente,
                                ProposicaoRecebida, ProposicaoTaView,
                                ReceberProposicao, ReciboProposicaoView,
                                RegimeTramitacaoCrud, RelatoriaCrud,
                                StatusTramitacaoCrud, TipoDocumentoCrud,
                                TipoFimRelatoriaCrud, TipoMateriaCrud,
                                TipoProposicaoCrud, TramitacaoCrud,
                                TramitacaoEmLoteView, UnidadeTramitacaoCrud,
                                proposicao_texto, recuperar_materia,
                                ExcluirTramitacaoEmLoteView,
                                RetornarProposicao,
                                MateriaPesquisaSimplesView,
                                DespachoInicialMultiCreateView,
                                get_zip_docacessorios, get_pdf_docacessorios,
                                configEtiquetaMateriaLegislativaCrud,
                                PesquisarStatusTramitacaoView)
from sapl.norma.views import NormaPesquisaSimplesView
from sapl.protocoloadm.views import (
    FichaPesquisaAdmView, FichaSelecionaAdmView
)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_impressos = [
    url(r'^materia/impressos/$',
        ImpressosView.as_view(),
        name='impressos'),
    url(r'^materia/impressos/etiqueta-pesquisa/$',
        EtiquetaPesquisaView.as_view(),
        name='impressos_etiqueta'),
    url(r'^materia/impressos/ficha-pesquisa/$',
        FichaPesquisaView.as_view(),
        name='impressos_ficha_pesquisa'),
    url(r'^materia/impressos/ficha-seleciona/$',
        FichaSelecionaView.as_view(),
        name='impressos_ficha_seleciona'),
    url(r'^materia/impressos/norma-pesquisa/$',
        NormaPesquisaSimplesView.as_view(),
        name='impressos_norma_pesquisa'),
    url(r'^materia/impressos/materia-pesquisa/$',
        MateriaPesquisaSimplesView.as_view(),
        name='impressos_materia_pesquisa'),
    url(r'^materia/impressos/ficha-pesquisa-adm/$',
        FichaPesquisaAdmView.as_view(),
        name='impressos_ficha_pesquisa_adm'),
    url(r'^materia/impressos/ficha-seleciona-adm/$',
        FichaSelecionaAdmView.as_view(),
        name='impressos_ficha_seleciona_adm'),
]

urlpatterns_materia = [

    # Esta customização substitui a url do crud desque que ela permaneça antes
    # da inclusão das urls de DespachoInicialCrud
    url(r'^materia/(?P<pk>\d+)/despachoinicial/create',
        DespachoInicialMultiCreateView.as_view(),
        name='despacho-inicial-multi'),

    url(r'^materia/', include(MateriaLegislativaCrud.get_urls() +
                              AnexadaCrud.get_urls() +
                              AutoriaCrud.get_urls() +
                              DespachoInicialCrud.get_urls() +
                              MateriaAssuntoCrud.get_urls() +
                              NumeracaoCrud.get_urls() +
                              LegislacaoCitadaCrud.get_urls() +
                              TramitacaoCrud.get_urls() +
                              RelatoriaCrud.get_urls() +
                              DocumentoAcessorioCrud.get_urls())),

    url(r'^materia/(?P<pk>[0-9]+)/create_simplificado$',
        CriarProtocoloMateriaView.as_view(),
        name='materia_create_simplificado'),
    url(r'^materia/recuperar-materia',
        recuperar_materia, name='recuperar_materia'),
    url(r'^materia/(?P<pk>[0-9]+)/ta$',
        MateriaTaView.as_view(), name='materia_ta'),


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

    url(r'^materia/(?P<pk>\d+)/autoria/multicreate',
        AutoriaMultiCreateView.as_view(),
        name='autoria_multicreate'),


    url(r'^materia/acessorio-em-lote', DocumentoAcessorioEmLoteView.as_view(),
        name='acessorio_em_lote'),
    url(r'^materia/(?P<pk>\d+)/anexada-em-lote', MateriaAnexadaEmLoteView.as_view(),
        name='anexada_em_lote'),
    url(r'^materia/primeira-tramitacao-em-lote',
        PrimeiraTramitacaoEmLoteView.as_view(),
        name='primeira_tramitacao_em_lote'),
    url(r'^materia/tramitacao-em-lote', TramitacaoEmLoteView.as_view(),
        name='tramitacao_em_lote'),
    url(r'^materia/excluir-tramitacao-em-lote', ExcluirTramitacaoEmLoteView.as_view(),
        name='excluir_tramitacao_em_lote'),
    url(r'^materia/docacessorio/zip/(?P<pk>\d+)$', get_zip_docacessorios,
        name='compress_docacessorios'),
    url(r'^materia/docacessorio/pdf/(?P<pk>\d+)$', get_pdf_docacessorios,
        name='merge_docacessorios')
]


urlpatterns_proposicao = [
    url(r'^proposicao/', include(ProposicaoCrud.get_urls())),
    url(r'^proposicao/recibo/(?P<pk>\d+)', ReciboProposicaoView.as_view(),
        name='recibo-proposicao'),
    url(r'^proposicao/receber/', ReceberProposicao.as_view(),
        name='receber-proposicao'),
    url(r'^proposicao/pendente/', ProposicaoPendente.as_view(),
        name='proposicao-pendente'),
    url(r'^proposicao/recebida/', ProposicaoRecebida.as_view(),
        name='proposicao-recebida'),
    url(r'^proposicao/devolvida/', ProposicaoDevolvida.as_view(),
        name='proposicao-devolvida'),
    url(r'^proposicao/confirmar/P(?P<hash>[0-9A-Fa-f]+)/'
        '(?P<pk>\d+)', ConfirmarProposicao.as_view(),
        name='proposicao-confirmar'),
    url(r'^sistema/proposicao/tipo/',
        include(TipoProposicaoCrud.get_urls())),

    url(r'^proposicao/(?P<pk>[0-9]+)/ta$',
        ProposicaoTaView.as_view(), name='proposicao_ta'),


    url(r'^proposicao/texto/(?P<pk>\d+)$', proposicao_texto,
        name='proposicao_texto'),
    url(r'^proposicao/(?P<pk>\d+)/retornar', RetornarProposicao.as_view(),
        name='retornar-proposicao'),

]

urlpatterns_sistema = [
    url(r'^sistema/assunto-materia/',
        include(AssuntoMateriaCrud.get_urls())),
    url(r'^sistema/proposicao/tipo/',
        include(TipoProposicaoCrud.get_urls())),
    url(r'^sistema/materia/tipo/', include(TipoMateriaCrud.get_urls())),
    url(r'^sistema/materia/regime-tramitacao/',
        include(RegimeTramitacaoCrud.get_urls())),
    url(r'^sistema/materia/tipo-documento/',
        include(TipoDocumentoCrud.get_urls())),
    url(r'^sistema/materia/tipo-fim-relatoria/',
        include(TipoFimRelatoriaCrud.get_urls())),
    url(r'^sistema/materia/unidade-tramitacao/',
        include(UnidadeTramitacaoCrud.get_urls())),
    url(r'^sistema/materia/origem/', include(OrigemCrud.get_urls())),

    url(r'^sistema/materia/status-tramitacao/', include(
        StatusTramitacaoCrud.get_urls()
    )),
    url(
        r'^sistema/materia/pesquisar-status-tramitacao/',
        PesquisarStatusTramitacaoView.as_view(),
        name="pesquisar_statustramitacao"
    ),

    url(r'^sistema/materia/orgao/', include(OrgaoCrud.get_urls())),
    url(r'^sistema/materia/config-etiqueta-materia-legislativas/',configEtiquetaMateriaLegislativaCrud, name="configEtiquetaMateriaLegislativaCrud"),
]

urlpatterns = urlpatterns_impressos + urlpatterns_materia + \
    urlpatterns_proposicao + urlpatterns_sistema
