from django.urls import path
from django.views.generic.base import TemplateView

from sapl.urls import urlpatterns as original_patterns

ptrn = [path("zzzz", TemplateView.as_view(template_name="index.html"), name="zzzz")]
urlpatterns = original_patterns + ptrn
