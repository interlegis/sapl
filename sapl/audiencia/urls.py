from django.conf.urls import include, url
from sapl.audiencia.views import (index, AudienciaCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^audiencia/', include(AudienciaCrud.get_urls())),
]