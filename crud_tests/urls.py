from django.conf.urls import include, url

from .views import country_crud

urlpatterns = [
    url(r'^countries/', include(country_crud.urls)),
]
