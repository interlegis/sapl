from django.conf.urls import include, url

from .views import CountryCrud

urlpatterns = [
    url(r'^country/', include(CountryCrud.get_urls(), 'stub_app')),
]
