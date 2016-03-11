from django.conf.urls import include, url

from lexml.views import LexmlProvedorCrud, LexmlPublicadorCrud

urlpatterns = [
    url(r'^sistema/lexml/provedor/',
        include(LexmlProvedorCrud.get_urls())),
    url(r'^sistema/lexml/publicador/',
        include(LexmlPublicadorCrud.get_urls())),
]
