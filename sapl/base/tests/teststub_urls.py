from django.conf.urls import url
from django.views.generic.base import TemplateView

from sapl.urls import urlpatterns as original_patterns

ptrn = [            url(r'^zzzz$',
                    TemplateView.as_view(
                        template_name='index.html'), name='zzzz')]

urlpatterns = original_patterns + ptrn
