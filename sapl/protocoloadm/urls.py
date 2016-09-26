from django.conf.urls import include, url

from sapl.protocoloadm.views import (AnularProtocoloAdmView,
                                     ComprovanteProtocoloView,
                                     CriarDocumentoProtocolo,
                                     DetailDocumentoAdministrativo,
                                     DocumentoAcessorioAdministrativoCrud,
                                     DocumentoAcessorioAdministrativoEditView,
                                     DocumentoAcessorioAdministrativoView,
                                     DocumentoAdministrativoCrud,
                                     PesquisarDocumentoAdministrativoView,
                                     ProtocoloDocumentoCrud,
                                     ProtocoloDocumentoView, ProtocoloListView,
                                     ProtocoloMateriaCrud,
                                     ProtocoloMateriaView,
                                     ProtocoloMostrarView,
                                     ProtocoloPesquisaView,
                                     StatusTramitacaoAdministrativoCrud,
                                     TipoDocumentoAdministrativoCrud,
                                     TipoInstituicaoCrud, TramitacaoAdmCrud,
                                     pesquisa_autores)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^protocoloadm/docadm/',
        include(DocumentoAdministrativoCrud.get_urls())),
    url(r'^protocoloadm/tipo-documento-adm/',
        include(TipoDocumentoAdministrativoCrud.get_urls())),
    url(r'^protocoloadm/doc-acessorio/',
        include(DocumentoAcessorioAdministrativoCrud.get_urls())),
    url(r'^protocoloadm/tramitacao-doc-adm/',
        include(TramitacaoAdmCrud.get_urls())),
    url(r'^protocoloadm/status-tramitacao-adm/',
        include(StatusTramitacaoAdministrativoCrud.get_urls())),
    url(r'^protocoloadm/tipo-instituicao/',
        include(TipoInstituicaoCrud.get_urls())),
    url(r'^protocoloadm/protocolo-doc/',
        include(ProtocoloDocumentoCrud.get_urls())),
    url(r'^protocoloadm/protocolo-mat/',
        include(ProtocoloMateriaCrud.get_urls()), name='protocolomat'),
    url(r'^protocoloadm/protocolo$',
        ProtocoloPesquisaView.as_view(), name='protocolo'),
    url(r'^protocoloadm/protocolo-list$',
        ProtocoloListView.as_view(), name='protocolo_list'),
    url(r'^protocoloadm/(?P<pk>\d+)/(?P<ano>\d+)/protocolo-mostrar$',
        ProtocoloMostrarView.as_view(), name='protocolo_mostrar'),
    url(r'^protocoloadm/anular-protocolo',
        AnularProtocoloAdmView.as_view(), name='anular_protocolo'),
    url(r'^protocoloadm/protocolar-doc',
        ProtocoloDocumentoView.as_view(), name='protocolar_doc'),
    url(r'^protocoloadm/protocolar-mat',
        ProtocoloMateriaView.as_view(), name='protocolar_mat'),
    url(r'^protocoloadm/pesq-doc-adm',
        PesquisarDocumentoAdministrativoView.as_view(), name='pesq_doc_adm'),
    url(r'^protocoloadm/doc-adm/(?P<pk>\d+)$',
        DetailDocumentoAdministrativo.as_view(), name='detail_doc_adm'),
    url(r'^protocoloadm/doc-ace-adm/(?P<pk>\d+)',
        DocumentoAcessorioAdministrativoView.as_view(), name='doc_ace_adm'),
    url(r'^protocoloadm/doc-ace-adm/edit/(?P<pk>\d+)/(?P<ano>\d+)',
        DocumentoAcessorioAdministrativoEditView.as_view(),
        name='doc_ace_adm_edit'),


    url(r'^protocoloadm/(?P<pk>\d+)/(?P<ano>\d+)/comprovante$',
        ComprovanteProtocoloView.as_view(), name='comprovante_protocolo'),
    url(r'^protocoloadm/(?P<pk>\d+)/(?P<ano>\d+)/criar-documento$',
        CriarDocumentoProtocolo.as_view(), name='criar_documento'),

    # FIXME: Usado para pesquisar autor
    # Melhor forma de fazer?
    # Deve mudar de app?
    url(r'^proposicao/pesquisar-autor',
        pesquisa_autores, name='pesquisar_autor'),
]
