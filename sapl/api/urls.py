from django.conf.urls import url

from sapl.api.views import TipoAutorContentOfModelContentTypeView

from .apps import AppConfig

app_name = AppConfig.name


# router = DefaultRouter()

urlpatterns = [
    url(r'^autor/possiveis-pelo-tipo/(?P<pk>[0-9]+)$',
        TipoAutorContentOfModelContentTypeView.as_view(),
        name='autores_possiveis_pelo_tipo'),
]

# urlpatterns += router.urls
