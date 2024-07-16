from django.urls.conf import re_path, include

from .views import CityCrud, CountryCrud

urlpatterns = [
    re_path(r'^country/', include(
        CountryCrud.get_urls() + CityCrud.get_urls(), 'stub_app')),
]
