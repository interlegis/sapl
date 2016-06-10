from django.conf.urls import include, url

from .views import CityCrud, CountryCrud

urlpatterns = [
    url(r'^country/', include(
        CountryCrud.get_urls() + CityCrud.get_urls(), 'stub_app')),
]
