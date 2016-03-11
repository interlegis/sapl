from django.conf.urls import include, url

from norma.views import (AssuntoNormaCrud, NormaEditView, NormaIncluirView,
                         NormaPesquisaView, NormaTaView, NormaTemporarioCrud,
                         PesquisaNormaListView, TipoNormaCrud)

# FIXME???? usar NormaCrud ????
norma_url_patterns, namespace = NormaTemporarioCrud.get_urls()

norma_url_patterns += [
    url(r'^norma/(?P<pk>[0-9]+)/ta$',
        NormaTaView.as_view(), name='ta')
]

urlpatterns = [
    url(r'^norma/', include(norma_url_patterns, namespace)),

    url(r'^sistema/norma/tipo/', include(TipoNormaCrud.get_urls())),
    url(r'^sistema/norma/assunto/', include(AssuntoNormaCrud.get_urls())),

    url(r'^norma/incluir$', NormaIncluirView.as_view(), name='norma_incluir'),
    url(r'^norma/(?P<pk>[0-9]+)/editar$',
        NormaEditView.as_view(), name='norma_editar'),
    url(r'^norma/pesquisa$',
        NormaPesquisaView.as_view(), name='norma_pesquisa'),
    url(r'^norma/pesquisa-resultado$',
        PesquisaNormaListView.as_view(), name='list_pesquisa_norma'),
]
