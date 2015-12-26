from django.conf.urls import include, url

from compilacao.urls import urlpatterns as __url__compilacao
from norma.views import (NormaIncluirView, assunto_norma_crud,
                         norma_temporario_crud, tipo_norma_crud)


norma_url_patterns = norma_temporario_crud.urlpatterns
# norma_url_patterns = norma_crud.urlpatterns + []

urlpatterns = [
    url(r'^norma/', include(norma_url_patterns,
                            norma_temporario_crud.namespace,
                            norma_temporario_crud.namespace)),

    url(r'^sistema/norma/tipo/', include(tipo_norma_crud.urls)),
    url(r'^sistema/norma/assunto/', include(assunto_norma_crud.urls)),

    url(r'^norma/incluir', NormaIncluirView.as_view(), name='norma-incluir'),
]
