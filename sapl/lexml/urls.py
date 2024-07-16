from django.urls.conf import path, include

from sapl.lexml.views import LexmlProvedorCrud, LexmlPublicadorCrud, lexml_request, request_search

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    path(r'^sistema/lexml/provedor/',
        include(LexmlProvedorCrud.get_urls())),
    path(r'^sistema/lexml/publicador/',
        include(LexmlPublicadorCrud.get_urls())),
    path(r'^sistema/lexml/request_search/(?P<keyword>[\w\-]+)/', request_search, name='lexml_search'),
    path(r'^sistema/lexml/oai', lexml_request, name='lexml_endpoint'),

]
