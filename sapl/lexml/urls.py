from django.conf.urls import include, url

from sapl.lexml.views import LexmlProvedorCrud, LexmlPublicadorCrud, lexml_request, request_search

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^sistema/lexml/provedor/',
        include(LexmlProvedorCrud.get_urls())),
    url(r'^sistema/lexml/publicador/',
        include(LexmlPublicadorCrud.get_urls())),
    url(r'^sistema/lexml/request_search/(?P<keyword>[\w\-]+)/', request_search, name='lexml_search'),
    url(r'^sistema/lexml/oai', lexml_request, name='lexml_endpoint'),

]
