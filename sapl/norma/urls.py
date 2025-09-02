from django.conf import settings
from django.urls import include, path, re_path

from sapl.norma.views import (AnexoNormaJuridicaCrud, AssuntoNormaCrud,
                              AutoriaNormaCrud, NormaCrud, NormaPesquisaView,
                              NormaRelacionadaCrud, NormaTaView,
                              PesquisarAssuntoNormaView, TipoNormaCrud,
                              TipoVinculoNormaJuridicaCrud, recuperar_norma,
                              recuperar_numero_norma)

from .apps import AppConfig

app_name = AppConfig.name


urlpatterns = [
    path(
        "norma/",
        include(
            NormaCrud.get_urls()
            + NormaRelacionadaCrud.get_urls()
            + AnexoNormaJuridicaCrud.get_urls()
            + AutoriaNormaCrud.get_urls()
        ),
    ),
    # Integração com Compilação
    path("norma/<int:pk>/ta", NormaTaView.as_view(), name="norma_ta"),
    path("sistema/norma/tipo/", include(TipoNormaCrud.get_urls())),
    path("sistema/norma/assunto/", include(AssuntoNormaCrud.get_urls())),
    re_path(
        r"^sistema/norma/pesquisar-assunto-norma/",
        PesquisarAssuntoNormaView.as_view(),
        name="pesquisar_assuntonorma",
    ),
    path("sistema/norma/vinculo/", include(TipoVinculoNormaJuridicaCrud.get_urls())),
    path("norma/pesquisar", NormaPesquisaView.as_view(), name="norma_pesquisa"),
    path("norma/recuperar-norma", recuperar_norma, name="recuperar_norma"),
    path(
        "norma/recuperar-numero-norma",
        recuperar_numero_norma,
        name="recuperar_numero_norma",
    ),
]
