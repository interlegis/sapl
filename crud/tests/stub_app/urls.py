from django.conf.urls import include, url

from .views import CountryCrud

urlpatterns = [
    url(r'^countries/', include(CountryCrud.get_urls())),
]
