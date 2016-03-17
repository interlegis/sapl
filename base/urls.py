from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import TemplateView

from .apps import AppConfig
from .views import CasaLegislativaTableAuxView, HelpView

app_name = AppConfig.name

urlpatterns = [
    url(r'^sistema/', TemplateView.as_view(template_name='sistema.html')),
    url(r'^ajuda/(?P<topic>\w+)$', HelpView.as_view(), name='help_topic'),
    url(r'^ajuda/', TemplateView.as_view(template_name='ajuda/index.html'),
        name='help_base'),
    url(r'^casa-legislativa$',
        CasaLegislativaTableAuxView.as_view(), name='casa_legislativa'),
]

# Fix a static asset finding error on Django 1.9 + gunicorn:
# http://stackoverflow.com/questions/35510373/
urlpatterns += staticfiles_urlpatterns()
