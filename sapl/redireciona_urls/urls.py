from django.conf.urls import url

from .views import (
    RedirecionaParlamentarDetailRedirectView,
    RedirecionaParlamentarListRedirectView)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^parlamentar/parlamentar_mostrar_proc$',
        RedirecionaParlamentarDetailRedirectView.as_view(),
        name='redireciona_parlamentar_detail'),
    url(r'^parlamentar/parlamentar_index_html$',
        RedirecionaParlamentarListRedirectView.as_view(),
        name='redireciona_parlamentar_list'),
]