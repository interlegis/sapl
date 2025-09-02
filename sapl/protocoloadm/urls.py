from django.urls import include, path, re_path

from sapl.protocoloadm.views import (AcompanhamentoConfirmarView,
                                     AcompanhamentoDocumentoView,
                                     AcompanhamentoExcluirView, AnexadoCrud,
                                     AnularProtocoloAdmView,
                                     ComprovanteProtocoloView,
                                     CriarDocumentoProtocolo,
                                     DesvincularDocumentoView,
                                     DesvincularMateriaView,
                                     DocumentoAcessorioAdministrativoCrud,
                                     DocumentoAdministrativoCrud,
                                     DocumentoAnexadoEmLoteView,
                                     PesquisarDocumentoAdministrativoView,
                                     PrimeiraTramitacaoEmLoteAdmView,
                                     ProtocoloDocumentoView,
                                     ProtocoloMateriaTemplateView,
                                     ProtocoloMateriaView,
                                     ProtocoloMostrarView,
                                     ProtocoloPesquisaView,
                                     StatusTramitacaoAdministrativoCrud,
                                     TipoDocumentoAdministrativoCrud,
                                     TramitacaoAdmCrud,
                                     TramitacaoEmLoteAdmView,
                                     VinculoDocAdminMateriaCrud,
                                     VinculoDocAdminMateriaEmLoteView,
                                     apaga_protocolos_view,
                                     atualizar_numero_documento,
                                     doc_texto_integral, get_pdf_docacessorios,
                                     recuperar_materia_protocolo)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_documento_administrativo = [
    path(
        "docadm/",
        include(
            DocumentoAdministrativoCrud.get_urls()
            + AnexadoCrud.get_urls()
            + TramitacaoAdmCrud.get_urls()
            + DocumentoAcessorioAdministrativoCrud.get_urls()
            + VinculoDocAdminMateriaCrud.get_urls()
        ),
    ),
    re_path(
        r"^docadm/pesq-doc-adm",
        PesquisarDocumentoAdministrativoView.as_view(),
        name="pesq_doc_adm",
    ),
    path(
        "docadm/texto_integral/<int:pk>", doc_texto_integral, name="doc_texto_integral"
    ),
    re_path(
        r"^docadm/(?P<pk>\d+)/anexado_em_lote",
        DocumentoAnexadoEmLoteView.as_view(),
        name="anexado_em_lote",
    ),
    re_path(
        r"^docadm/(?P<pk>\d+)/vinculo-em-lote",
        VinculoDocAdminMateriaEmLoteView.as_view(),
        name="vinculodocadminmateria_em_lote",
    ),
    path(
        "docadm/documentoacessorioadministrativo/pdf/<int:pk>",
        get_pdf_docacessorios,
        name="merge_docacessorios",
    ),
]

urlpatterns_protocolo = [
    #    url(r'^protocoloadm/protocolo-doc/',
    #        include(ProtocoloDocumentoCrud.get_urls())),
    #    url(r'^protocoloadm/protocolo-mat/',
    #        include(ProtocoloMateriaCrud.get_urls()), name='protocolomat'),
    # url(r'^protocoloadm/protocolo-list$',
    #    ProtocoloListView.as_view(), name='protocolo_list'),
    path("protocoloadm/", ProtocoloPesquisaView.as_view(), name="protocolo"),
    re_path(
        r"^protocoloadm/protocolar-doc",
        ProtocoloDocumentoView.as_view(),
        name="protocolar_doc",
    ),
    path(
        "protocoloadm/<int:pk>/protocolo-mostrar",
        ProtocoloMostrarView.as_view(),
        name="protocolo_mostrar",
    ),
    path(
        "docadm/<int:pk>/acompanhar-documento/",
        AcompanhamentoDocumentoView.as_view(),
        name="acompanhar_documento",
    ),
    path(
        "docadm/<int:pk>/acompanhar-confirmar",
        AcompanhamentoConfirmarView.as_view(),
        name="acompanhar_confirmar",
    ),
    path(
        "docadm/<int:pk>/acompanhar-excluir",
        AcompanhamentoExcluirView.as_view(),
        name="acompanhar_excluir",
    ),
    path(
        "protocoloadm/<int:pk>/continuar",
        ProtocoloMateriaTemplateView.as_view(),
        name="materia_continuar",
    ),
    re_path(
        r"^protocoloadm/anular-protocolo",
        AnularProtocoloAdmView.as_view(),
        name="anular_protocolo",
    ),
    re_path(
        r"^protocoloadm/desvincular-documento",
        DesvincularDocumentoView.as_view(),
        name="desvincular_documento",
    ),
    re_path(
        r"^protocoloadm/desvincular-materia",
        DesvincularMateriaView.as_view(),
        name="desvincular_materia",
    ),
    re_path(
        r"^protocoloadm/protocolar-mat",
        ProtocoloMateriaView.as_view(),
        name="protocolar_mat",
    ),
    path(
        "protocoloadm/<int:pk>/comprovante",
        ComprovanteProtocoloView.as_view(),
        name="comprovante_protocolo",
    ),
    path(
        "protocoloadm/<int:pk>/criar-documento",
        CriarDocumentoProtocolo.as_view(),
        name="criar_documento",
    ),
    path(
        "protocoloadm/atualizar_numero_documento",
        atualizar_numero_documento,
        name="atualizar_numero_documento",
    ),
    re_path(
        r"^protocoloadm/recuperar-materia",
        recuperar_materia_protocolo,
        name="recuperar_materia_protocolo",
    ),
    re_path(
        r"^protocoloadm/primeira-tramitacao-em-lote",
        PrimeiraTramitacaoEmLoteAdmView.as_view(),
        name="primeira_tramitacao_em_lote_docadm",
    ),
    re_path(
        r"^protocoloadm/tramitacao-em-lote",
        TramitacaoEmLoteAdmView.as_view(),
        name="tramitacao_em_lote_docadm",
    ),
    re_path(
        r"^protocoloadm/apaga_protocolos",
        apaga_protocolos_view,
        name="apaga_protocolos_view",
    ),
]

urlpatterns_sistema = [
    path(
        "sistema/tipo-documento-adm/",
        include(TipoDocumentoAdministrativoCrud.get_urls()),
    ),
    path(
        "sistema/status-tramitacao-adm/",
        include(StatusTramitacaoAdministrativoCrud.get_urls()),
    ),
]

urlpatterns = (
    urlpatterns_documento_administrativo + urlpatterns_protocolo + urlpatterns_sistema
)
