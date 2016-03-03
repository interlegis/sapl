"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from django.conf.urls import url
from django.views.generic.base import TemplateView

from .views import CasaLegislativaTableAuxView, HelpView

urlpatterns = [
    url(r'^sistema/', TemplateView.as_view(template_name='sistema.html')),
    url(r'^ajuda/(?P<topic>\w+)$', HelpView.as_view(), name='help_topic'),
    url(r'^ajuda/', TemplateView.as_view(template_name='ajuda/index.html'),
        name='help_base'),
    url(r'^casa-legislativa$',
        CasaLegislativaTableAuxView.as_view(), name='casa_legislativa'),
]
