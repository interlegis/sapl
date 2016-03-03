"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from django.conf.urls import include, url

from .views import country_crud

urlpatterns = [
    url(r'^countries/', include(country_crud.urls)),
]
