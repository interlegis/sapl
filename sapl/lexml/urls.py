from django.conf.urls import include, url

from sapl.lexml.views import LexmlProvedorCrud, LexmlPublicadorCrud

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^sistema/lexml/provedor/',
        include(LexmlProvedorCrud.get_urls())),
    url(r'^sistema/lexml/publicador/',
        include(LexmlPublicadorCrud.get_urls())),
]
