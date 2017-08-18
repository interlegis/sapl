from django.conf.urls import patterns, url
from django.views.generic.base import TemplateView

from sapl.urls import urlpatterns as original_patterns

urlpatterns = original_patterns + patterns
('', url(r'^zzzz$', TemplateView.as_view(
    template_name='index.html'), name='zzzz'))
