from django.conf.urls import url, include
from sapl.api.views import AutorListView

from .apps import AppConfig


app_name = AppConfig.name


# router = DefaultRouter()

# urlpatterns += router.urls


urlpatterns_api = [
    # url(r'^$', api_root),
    url(r'^autor',
        AutorListView.as_view(),
        name='autor_list'),
]

urlpatterns = [
    url(r'^api/', include(urlpatterns_api))
]
