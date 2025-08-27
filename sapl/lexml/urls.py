from django.urls import include, path, re_path

from sapl.lexml.views import LexmlProvedorCrud, LexmlPublicadorCrud, lexml_request, request_search

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    path('sistema/lexml/provedor/',
        include(LexmlProvedorCrud.get_urls())),
    path('sistema/lexml/publicador/',
        include(LexmlPublicadorCrud.get_urls())),
    re_path(r'^sistema/lexml/request_search/(?P<keyword>[\w\-]+)/', request_search, name='lexml_search'),
    re_path(r'^sistema/lexml/oai', lexml_request, name='lexml_endpoint'),

]
