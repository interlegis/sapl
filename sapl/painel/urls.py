from django.urls import path

from .apps import AppConfig
from .views import (cronometro_painel, get_dados_painel, painel_mensagem_view,
                    painel_parlamentar_view, painel_view, painel_votacao_view,
                    switch_painel, verifica_painel, votante_view)

app_name = AppConfig.name

urlpatterns = [
    path('painel-principal/<int:pk>', painel_view,
        name="painel_principal"),
    path('painel/<int:pk>/dados', get_dados_painel, name='dados_painel'),
    path('painel/mensagem', painel_mensagem_view, name="painel_mensagem"),
    path('painel/parlamentar', painel_parlamentar_view,
        name='painel_parlamentar'),
    path('painel/switch-painel', switch_painel,
        name="switch_painel"),
    path('painel/votacao', painel_votacao_view, name='painel_votacao'),
    path('painel/verifica-painel', verifica_painel,
        name="verifica_painel"),
    path('painel/cronometro', cronometro_painel, name='cronometro_painel'),
    # url(r'^painel/cronometro$', include(CronometroPainelCrud.get_urls())),

    path('voto-individual/', votante_view,
        name='voto_individual'),
]
