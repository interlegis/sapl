from django.urls.conf import path, include
from sapl.audiencia.views import (
    index, AudienciaCrud, AnexoAudienciaPublicaCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    path(r'^audiencia/', include(AudienciaCrud.get_urls() +
                                 AnexoAudienciaPublicaCrud.get_urls())),
]
