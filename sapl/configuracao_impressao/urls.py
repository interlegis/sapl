from django.conf.urls import include, url
from sapl.configuracao_impressao.views import (ConfiguracaoImpressaoCrud)
from .apps import AppConfig


app_name = AppConfig.name
urlpatterns = [
    url(r'^configuracao_impressao/', include(ConfiguracaoImpressaoCrud.get_urls())),
]
