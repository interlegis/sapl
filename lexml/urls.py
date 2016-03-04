"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from django.conf.urls import include, url

from lexml.views import lexml_provedor_crud, lexml_publicador_crud

urlpatterns = [
    url(r'^sistema/lexml/provedor/', include(lexml_provedor_crud.urls)),
    url(r'^sistema/lexml/publicador/', include(lexml_publicador_crud.urls)),
]
