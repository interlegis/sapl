from django.conf.urls import include, url

from sapl.norma.views import (AssuntoNormaCrud, NormaCrud, NormaPesquisaView,
                              TipoNormaCrud, NormaTaView)

from .apps import AppConfig

app_name = AppConfig.name


urlpatterns = [
    url(r'^norma/', include(NormaCrud.get_urls())),

    # Integração com Compilação
    url(r'^norma/(?P<pk>[0-9]+)/ta$', NormaTaView.as_view(), name='norma_ta'),

    url(r'^sistema/norma/tipo/', include(TipoNormaCrud.get_urls())),
    url(r'^sistema/norma/assunto/', include(AssuntoNormaCrud.get_urls())),

    url(r'^norma/pesquisar$',
        NormaPesquisaView.as_view(), name='norma_pesquisa'),
]
