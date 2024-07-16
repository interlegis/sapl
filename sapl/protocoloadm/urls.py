from django.urls.conf import path, include

from sapl.protocoloadm.views import (AcompanhamentoDocumentoView,
                                     AcompanhamentoConfirmarView,
                                     AcompanhamentoExcluirView,
                                     AnularProtocoloAdmView,
                                     ComprovanteProtocoloView,
                                     CriarDocumentoProtocolo,
                                     DocumentoAcessorioAdministrativoCrud,
                                     DocumentoAdministrativoCrud,
                                     PesquisarDocumentoAdministrativoView,
                                     ProtocoloDocumentoView,
                                     ProtocoloMateriaTemplateView,
                                     ProtocoloMateriaView,
                                     ProtocoloMostrarView,
                                     ProtocoloPesquisaView,
                                     StatusTramitacaoAdministrativoCrud,
                                     recuperar_materia_protocolo,
                                     TipoDocumentoAdministrativoCrud,
                                     TramitacaoAdmCrud,
                                     atualizar_numero_documento,
                                     doc_texto_integral,
                                     DesvincularDocumentoView,
                                     DesvincularMateriaView,
                                     AnexadoCrud, DocumentoAnexadoEmLoteView,
                                     PrimeiraTramitacaoEmLoteAdmView,
                                     TramitacaoEmLoteAdmView,
                                     apaga_protocolos_view,
                                     VinculoDocAdminMateriaCrud,
                                     VinculoDocAdminMateriaEmLoteView,
                                     get_pdf_docacessorios)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_documento_administrativo = [
    path(r'^docadm/',
        include(DocumentoAdministrativoCrud.get_urls() +
                AnexadoCrud.get_urls() +
                TramitacaoAdmCrud.get_urls() +
                DocumentoAcessorioAdministrativoCrud.get_urls() +
                VinculoDocAdminMateriaCrud.get_urls())),

    path(r'^docadm/pesq-doc-adm',
        PesquisarDocumentoAdministrativoView.as_view(), name='pesq_doc_adm'),

    path(r'^docadm/texto_integral/(?P<pk>\d+)$', doc_texto_integral,
        name='doc_texto_integral'),

    path(r'^docadm/(?P<pk>\d+)/anexado_em_lote', DocumentoAnexadoEmLoteView.as_view(),
        name='anexado_em_lote'),
    path(r'^docadm/(?P<pk>\d+)/vinculo-em-lote', VinculoDocAdminMateriaEmLoteView.as_view(),
        name='vinculodocadminmateria_em_lote'),
    path(r'^docadm/documentoacessorioadministrativo/pdf/(?P<pk>\d+)$', get_pdf_docacessorios,
        name='merge_docacessorios')
]

urlpatterns_protocolo = [

    #    path(r'^protocoloadm/protocolo-doc/',
    #        include(ProtocoloDocumentoCrud.get_urls())),
    #    path(r'^protocoloadm/protocolo-mat/',
    #        include(ProtocoloMateriaCrud.get_urls()), name='protocolomat'),
    # url(r'^protocoloadm/protocolo-list$',
    #    ProtocoloListView.as_view(), name='protocolo_list'),

    path(r'^protocoloadm/$',
        ProtocoloPesquisaView.as_view(), name='protocolo'),

    path(r'^protocoloadm/protocolar-doc',
        ProtocoloDocumentoView.as_view(), name='protocolar_doc'),


    path(r'^protocoloadm/(?P<pk>\d+)/protocolo-mostrar$',
        ProtocoloMostrarView.as_view(), name='protocolo_mostrar'),

    path(r'^docadm/(?P<pk>\d+)/acompanhar-documento/$',
        AcompanhamentoDocumentoView.as_view(), name='acompanhar_documento'),
    path(r'^docadm/(?P<pk>\d+)/acompanhar-confirmar$',
        AcompanhamentoConfirmarView.as_view(),
        name='acompanhar_confirmar'),
    path(r'^docadm/(?P<pk>\d+)/acompanhar-excluir$',
        AcompanhamentoExcluirView.as_view(),
        name='acompanhar_excluir'),



    path(r'^protocoloadm/(?P<pk>\d+)/continuar$',
        ProtocoloMateriaTemplateView.as_view(), name='materia_continuar'),


    path(r'^protocoloadm/anular-protocolo',
        AnularProtocoloAdmView.as_view(), name='anular_protocolo'),
    path(r'^protocoloadm/desvincular-documento',
        DesvincularDocumentoView.as_view(), name='desvincular_documento'),
    path(r'^protocoloadm/desvincular-materia',
        DesvincularMateriaView.as_view(), name='desvincular_materia'),
    path(r'^protocoloadm/protocolar-mat',
        ProtocoloMateriaView.as_view(), name='protocolar_mat'),

    path(r'^protocoloadm/(?P<pk>\d+)/comprovante$',
        ComprovanteProtocoloView.as_view(), name='comprovante_protocolo'),
    path(r'^protocoloadm/(?P<pk>\d+)/criar-documento$',
        CriarDocumentoProtocolo.as_view(), name='criar_documento'),

    path(r'^protocoloadm/atualizar_numero_documento$',
        atualizar_numero_documento, name='atualizar_numero_documento'),
    path(r'^protocoloadm/recuperar-materia',
        recuperar_materia_protocolo, name='recuperar_materia_protocolo'),

    path(r'^protocoloadm/primeira-tramitacao-em-lote',
        PrimeiraTramitacaoEmLoteAdmView.as_view(),
        name='primeira_tramitacao_em_lote_docadm'),

    path(r'^protocoloadm/tramitacao-em-lote', TramitacaoEmLoteAdmView.as_view(),
        name='tramitacao_em_lote_docadm'),

    path(r'^protocoloadm/apaga_protocolos', apaga_protocolos_view,
        name='apaga_protocolos_view'),


]

urlpatterns_sistema = [
    path(r'^sistema/tipo-documento-adm/',
        include(TipoDocumentoAdministrativoCrud.get_urls())),
    path(r'^sistema/status-tramitacao-adm/',
        include(StatusTramitacaoAdministrativoCrud.get_urls())),
]

urlpatterns = (urlpatterns_documento_administrativo +
               urlpatterns_protocolo +
               urlpatterns_sistema)
