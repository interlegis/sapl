from django.urls import include, path

from .views import CityCrud, CountryCrud

urlpatterns = [
    path("country/", include(CountryCrud.get_urls() + CityCrud.get_urls(), "stub_app")),
]
