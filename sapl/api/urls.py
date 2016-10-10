from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from sapl.api.views import TipoAutorContentOfModelContentTypeView

from .apps import AppConfig


app_name = AppConfig.name


# router = DefaultRouter()

urlpatterns = [
    url(r'^autor/possiveis/(?P<pk>[0-9]*)$',
        TipoAutorContentOfModelContentTypeView.as_view(),
        name='autores_possiveis_pelo_tipo'),
]

# urlpatterns += router.urls
