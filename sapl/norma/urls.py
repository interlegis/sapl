from django.conf import settings
from django.conf.urls import include, url

from sapl.norma.views import (AnexoNormaJuridicaCrud, AssuntoNormaCrud,
                              NormaCrud, NormaPesquisaView,
                              NormaRelacionadaCrud, NormaTaView, TipoNormaCrud,
                              TipoVinculoNormaJuridicaCrud, recuperar_norma,
                              recuperar_numero_norma, AutoriaNormaCrud,
                              PesquisarAssuntoNormaView)


from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    url(r'^norma/', include(NormaCrud.get_urls() +
                            NormaRelacionadaCrud.get_urls() +
                            AnexoNormaJuridicaCrud.get_urls() +
                            AutoriaNormaCrud.get_urls())),

    # Integração com Compilação
    url(r'^norma/(?P<pk>[0-9]+)/ta$', NormaTaView.as_view(), name='norma_ta'),
    url(r'^sistema/norma/tipo/', include(TipoNormaCrud.get_urls())),

    url(r'^sistema/norma/assunto/', include(AssuntoNormaCrud.get_urls())),
    url(
        r'^sistema/norma/pesquisar-assunto-norma/',
        PesquisarAssuntoNormaView.as_view(), name="pesquisar_assuntonorma"
    ),

    url(r'^sistema/norma/vinculo/', include(
        TipoVinculoNormaJuridicaCrud.get_urls())),

    url(r'^norma/pesquisar$',
        NormaPesquisaView.as_view(), name='norma_pesquisa'),

    url(r'^norma/recuperar-norma$', recuperar_norma, name="recuperar_norma"),
    url(r'^norma/recuperar-numero-norma$', recuperar_numero_norma,
        name="recuperar_numero_norma"),
]
