from django.conf.urls import url
from django.views.generic.base import TemplateView

from .views import HelpView

urlpatterns = [
    url(r'^sistema/', TemplateView.as_view(template_name='sistema.html')),
    url(r'^ajuda/(?P<topic>\w+)$', HelpView.as_view(), name='help_topic'),
    url(r'^ajuda/', TemplateView.as_view(template_name='ajuda/index.html'),
        name='help_base'),
]
