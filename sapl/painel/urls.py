from django.conf.urls import url

from .apps import AppConfig
from .views import (cronometro_painel, get_dados_painel, painel_view,
                    switch_painel, verifica_painel, votante_view)

app_name = AppConfig.name

urlpatterns = [
    url(r'^painel-principal/(?P<pk>\d+)$', painel_view,
        name="painel_principal"),
    url(r'^painel/(?P<pk>\d+)/dados$', get_dados_painel, name='dados_painel'),
    url(r'^painel/switch-painel$', switch_painel,
        name="switch_painel"),
    url(r'^painel/verifica-painel$', verifica_painel,
        name="verifica_painel"),
    url(r'^painel/cronometro$', cronometro_painel, name='cronometro_painel'),
    # url(r'^painel/cronometro$', include(CronometroPainelCrud.get_urls())),

    url(r'^voto-individual/$', votante_view,
        name='voto_individual'),
]
