from django.urls.conf import path

from .apps import AppConfig
from .views import (cronometro_painel, get_dados_painel, painel_mensagem_view,
                    painel_parlamentar_view, painel_view, painel_votacao_view,
                    switch_painel, verifica_painel, votante_view)

app_name = AppConfig.name

urlpatterns = [
    path(r'^painel-principal/(?P<pk>\d+)$', painel_view,
        name="painel_principal"),
    path(r'^painel/(?P<pk>\d+)/dados$', get_dados_painel, name='dados_painel'),
    path(r'^painel/mensagem$', painel_mensagem_view, name="painel_mensagem"),
    path(r'^painel/parlamentar$', painel_parlamentar_view,
        name='painel_parlamentar'),
    path(r'^painel/switch-painel$', switch_painel,
        name="switch_painel"),
    path(r'^painel/votacao$', painel_votacao_view, name='painel_votacao'),
    path(r'^painel/verifica-painel$', verifica_painel,
        name="verifica_painel"),
    path(r'^painel/cronometro$', cronometro_painel, name='cronometro_painel'),
    # url(r'^painel/cronometro$', include(CronometroPainelCrud.get_urls())),

    path(r'^voto-individual/$', votante_view,
        name='voto_individual'),
]
