from django.urls.conf import re_path

from .apps import AppConfig
from .views import (cronometro_painel, get_dados_painel, painel_mensagem_view,
                    painel_parlamentar_view, painel_view, painel_votacao_view,
                    switch_painel, verifica_painel, votante_view)

app_name = AppConfig.name

urlpatterns = [
    re_path(r'^painel-principal/(?P<pk>\d+)$', painel_view,
        name="painel_principal"),
    re_path(r'^painel/(?P<pk>\d+)/dados$', get_dados_painel, name='dados_painel'),
    re_path(r'^painel/mensagem$', painel_mensagem_view, name="painel_mensagem"),
    re_path(r'^painel/parlamentar$', painel_parlamentar_view,
        name='painel_parlamentar'),
    re_path(r'^painel/switch-painel$', switch_painel,
        name="switch_painel"),
    re_path(r'^painel/votacao$', painel_votacao_view, name='painel_votacao'),
    re_path(r'^painel/verifica-painel$', verifica_painel,
        name="verifica_painel"),
    re_path(r'^painel/cronometro$', cronometro_painel, name='cronometro_painel'),
    # url(r'^painel/cronometro$', include(CronometroPainelCrud.get_urls())),

    re_path(r'^voto-individual/$', votante_view,
        name='voto_individual'),
]
