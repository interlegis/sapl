from django.urls.conf import path, include

from .views import CityCrud, CountryCrud

urlpatterns = [
    path(r'^country/', include(
        CountryCrud.get_urls() + CityCrud.get_urls(), 'stub_app')),
]
