from django.conf.urls import include, url

from norma.views import assunto_norma_crud, tipo_norma_crud

urlpatterns = [
    url(r'^sistema/norma/tipo/', include(tipo_norma_crud.urls)),
    url(r'^sistema/norma/assunto/', include(assunto_norma_crud.urls)),
]
