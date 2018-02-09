from django.conf.urls import include, url
from sapl.materia.views import (AcompanhamentoConfirmarView,
                                AcompanhamentoExcluirView,
                                AcompanhamentoMateriaView, AnexadaCrud,
                                AssuntoMateriaCrud, AutoriaCrud,
                                AutoriaMultiCreateView, ConfirmarProposicao,
                                CriarProtocoloMateriaView, DespachoInicialCrud,
                                DocumentoAcessorioCrud,
                                DocumentoAcessorioEmLoteView,
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
                                proposicao_texto, recuperar_materia)
from sapl.norma.views import NormaPesquisaSimplesView

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
]

urlpatterns_materia = [
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
    url(r'^materia/recuperar-materia', recuperar_materia),
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
    url(r'^materia/primeira-tramitacao-em-lote',
        PrimeiraTramitacaoEmLoteView.as_view(),
        name='primeira_tramitacao_em_lote'),
    url(r'^materia/tramitacao-em-lote', TramitacaoEmLoteView.as_view(),
        name='tramitacao_em_lote'),
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
]

urlpatterns_sistema = [
    url(r'^sistema/assunto-materia',
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
    url(r'^sistema/materia/status-tramitacao/',
        include(StatusTramitacaoCrud.get_urls())),
    url(r'^sistema/materia/orgao/', include(OrgaoCrud.get_urls())),
]

urlpatterns = urlpatterns_impressos + urlpatterns_materia + \
    urlpatterns_proposicao + urlpatterns_sistema
