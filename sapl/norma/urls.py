from django.conf import settings
from django.urls.conf import re_path, include

from sapl.norma.views import (AnexoNormaJuridicaCrud, AssuntoNormaCrud,
                              NormaCrud, NormaPesquisaView,
                              NormaRelacionadaCrud, NormaTaView, TipoNormaCrud,
                              TipoVinculoNormaJuridicaCrud, recuperar_norma,
                              recuperar_numero_norma, AutoriaNormaCrud,
                              PesquisarAssuntoNormaView)


from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    re_path(r'^norma/', include(NormaCrud.get_urls() +
                            NormaRelacionadaCrud.get_urls() +
                            AnexoNormaJuridicaCrud.get_urls() +
                            AutoriaNormaCrud.get_urls())),

    # Integração com Compilação
    re_path(r'^norma/(?P<pk>[0-9]+)/ta$', NormaTaView.as_view(), name='norma_ta'),
    re_path(r'^sistema/norma/tipo/', include(TipoNormaCrud.get_urls())),

    re_path(r'^sistema/norma/assunto/', include(AssuntoNormaCrud.get_urls())),
    re_path(
        r'^sistema/norma/pesquisar-assunto-norma/',
        PesquisarAssuntoNormaView.as_view(), name="pesquisar_assuntonorma"
    ),

    re_path(r'^sistema/norma/vinculo/', include(
        TipoVinculoNormaJuridicaCrud.get_urls())),

    re_path(r'^norma/pesquisar$',
        NormaPesquisaView.as_view(), name='norma_pesquisa'),

    re_path(r'^norma/recuperar-norma$', recuperar_norma, name="recuperar_norma"),
    re_path(r'^norma/recuperar-numero-norma$', recuperar_numero_norma,
        name="recuperar_numero_norma"),
]
