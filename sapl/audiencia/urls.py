from django.conf.urls import include, url
from sapl.audiencia.views import (index)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^audiencia/', index, name='index'),
]