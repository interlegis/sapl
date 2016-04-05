from django.conf.urls import url

from .apps import AppConfig
from .views import controlador_painel  # CronometroPainelCrud,
from .views import (cronometro_painel, get_dados_painel, painel_mensagem_view,
                    painel_parlamentares_view, painel_view,
                    painel_votacao_view)

app_name = AppConfig.name

urlpatterns = [
    url(r'^(?P<pk>\d+)/painel$', painel_view, name="painel_principal"),
    url(r'^painel/(?P<pk>\d+)/dados$', get_dados_painel, name='dados_painel'),
    url(r'^painel/controlador$',
        controlador_painel, name='painel_controlador'),
    url(r'^painel/mensagem$', painel_mensagem_view, name="painel_mensagem"),
    url(r'^painel/parlamentares$', painel_parlamentares_view,
        name='painel_parlamentares'),
    url(r'^painel/votacao$', painel_votacao_view, name='painel_votacao'),
    url(r'^painel/cronometro$', cronometro_painel, name='cronometro_painel'),
    # url(r'^painel/cronometro$', include(CronometroPainelCrud.get_urls())),
]
