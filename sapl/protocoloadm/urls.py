from django.conf.urls import include, url
from sapl.protocoloadm.views import (AnularProtocoloAdmView,
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
                                     TipoDocumentoAdministrativoCrud,
                                     TramitacaoAdmCrud,
                                     atualizar_numero_documento,
                                     doc_texto_integral)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_documento_administrativo = [
    url(r'^docadm/',
        include(DocumentoAdministrativoCrud.get_urls() +
                TramitacaoAdmCrud.get_urls() +
                DocumentoAcessorioAdministrativoCrud.get_urls())),

    url(r'^docadm/pesq-doc-adm',
        PesquisarDocumentoAdministrativoView.as_view(), name='pesq_doc_adm'),

    url(r'^docadm/texto_integral/(?P<pk>\d+)$', doc_texto_integral,
        name='doc_texto_integral'),
]

urlpatterns_protocolo = [

    #    url(r'^protocoloadm/protocolo-doc/',
    #        include(ProtocoloDocumentoCrud.get_urls())),
    #    url(r'^protocoloadm/protocolo-mat/',
    #        include(ProtocoloMateriaCrud.get_urls()), name='protocolomat'),
    # url(r'^protocoloadm/protocolo-list$',
    #    ProtocoloListView.as_view(), name='protocolo_list'),

    url(r'^protocoloadm/$',
        ProtocoloPesquisaView.as_view(), name='protocolo'),

    url(r'^protocoloadm/protocolar-doc',
        ProtocoloDocumentoView.as_view(), name='protocolar_doc'),


    url(r'^protocoloadm/(?P<pk>\d+)/protocolo-mostrar$',
        ProtocoloMostrarView.as_view(), name='protocolo_mostrar'),



    url(r'^protocoloadm/(?P<pk>\d+)/continuar$',
        ProtocoloMateriaTemplateView.as_view(), name='materia_continuar'),


    url(r'^protocoloadm/anular-protocolo',
        AnularProtocoloAdmView.as_view(), name='anular_protocolo'),
    url(r'^protocoloadm/protocolar-mat',
        ProtocoloMateriaView.as_view(), name='protocolar_mat'),

    url(r'^protocoloadm/(?P<pk>\d+)/comprovante$',
        ComprovanteProtocoloView.as_view(), name='comprovante_protocolo'),
    url(r'^protocoloadm/(?P<pk>\d+)/criar-documento$',
        CriarDocumentoProtocolo.as_view(), name='criar_documento'),

    url(r'^protocoloadm/atualizar_numero_documento$',
        atualizar_numero_documento, name='atualizar_numero_documento'),


]

urlpatterns_sistema = [
    url(r'^sistema/tipo-documento-adm/',
        include(TipoDocumentoAdministrativoCrud.get_urls())),
    url(r'^sistema/status-tramitacao-adm/',
        include(StatusTramitacaoAdministrativoCrud.get_urls())),

    # FIXME: Usado para pesquisar autor- SOLUÇÃO-foi transformado em api/autor
    # Melhor forma de fazer?
    # Deve mudar de app?
    # url(r'^protocoloadm/pesquisar-autor',
    #    pesquisa_autores, name='pesquisar_autor'),
]

urlpatterns = (urlpatterns_documento_administrativo +
               urlpatterns_protocolo +
               urlpatterns_sistema)
