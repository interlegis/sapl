from django.conf.urls import include, url
from protocoloadm.views import (anular_protocolo_crud,
                                documento_acessorio_administrativo_crud,
                                documento_administrativo_crud,
                                protocolo_documento_crud,
                                protocolo_materia_crud,
                                status_tramitacao_administrativo_crud,
                                tipo_documento_administrativo_crud,
                                tramitacao_administrativo_crud)

urlpatterns = [
    url(r'^protocoloadm/docadm/', include(documento_administrativo_crud.urls)),
    url(r'^protocoloadm/tipo-documento-adm/',
        include(tipo_documento_administrativo_crud.urls)),
    url(r'^protocoloadm/doc-acessorio/',
        include(documento_acessorio_administrativo_crud.urls)),
    url(r'^protocoloadm/status-tramitacao-adm/',
        include(status_tramitacao_administrativo_crud.urls)),
    url(r'^protocoloadm/tramitacao-adm/',
        include(tramitacao_administrativo_crud.urls)),
    url(r'^protocoloadm/protocolo-doc/',
        include(protocolo_documento_crud.urls)),
    url(r'^protocoloadm/protocolo-mat/', include(protocolo_materia_crud.urls)),
    url(r'^protocoloadm/anular-protocolo/',
        include(anular_protocolo_crud.urls)),

]
