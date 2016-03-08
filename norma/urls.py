from django.conf.urls import include, url

from norma.views import (NormaEditView, NormaIncluirView, NormaPesquisaView,
                         NormaTaView, PesquisaNormaListView,
                         assunto_norma_crud, norma_temporario_crud,
                         tipo_norma_crud)

# norma_url_patterns = norma_crud.urlpatterns + []
norma_url_patterns = norma_temporario_crud.urlpatterns + [
    url(r'^norma/(?P<pk>[0-9]+)/ta$',
        NormaTaView.as_view(), name='ta')
]

urlpatterns = [
    url(r'^norma/', include(norma_url_patterns,
                            norma_temporario_crud.namespace,
                            norma_temporario_crud.namespace)),

    url(r'^sistema/norma/tipo/', include(tipo_norma_crud.urls)),
    url(r'^sistema/norma/assunto/', include(assunto_norma_crud.urls)),

    url(r'^norma/incluir$', NormaIncluirView.as_view(), name='norma_incluir'),
    url(r'^norma/(?P<pk>[0-9]+)/editar$',
        NormaEditView.as_view(), name='norma_editar'),
    url(r'^norma/pesquisa$',
     NormaPesquisaView.as_view(), name='norma_pesquisa'),
    url(r'^norma/pesquisa-resultado$',
     PesquisaNormaListView.as_view(), name='list_pesquisa_norma'),
]
