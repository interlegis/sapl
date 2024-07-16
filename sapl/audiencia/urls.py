from django.urls.conf import re_path, include
from sapl.audiencia.views import (
    index, AudienciaCrud, AnexoAudienciaPublicaCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    re_path(r'^audiencia/', include(AudienciaCrud.get_urls() +
                                 AnexoAudienciaPublicaCrud.get_urls())),
]
