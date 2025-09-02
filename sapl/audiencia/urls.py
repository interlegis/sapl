from django.urls import include, path

from sapl.audiencia.views import (AnexoAudienciaPublicaCrud, AudienciaCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    path(
        "audiencia/",
        include(AudienciaCrud.get_urls() + AnexoAudienciaPublicaCrud.get_urls()),
    ),
]
