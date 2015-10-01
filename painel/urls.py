from django.conf.urls import include, url

from .views import (controlador_painel, cronometro_painel_crud, json_presenca,
                    json_votacao, painel_mensagem_view,
                    painel_parlamentares_view, painel_view,
                    painel_votacao_view)

urlpatterns = [
    url(r'^sistema/painel$', painel_view),
    url(r'^sistema/painel/controlador',
        controlador_painel, name='controlador_painel'),
    url(r'^sistema/painel/mensagem', painel_mensagem_view),
    url(r'^sistema/painel/parlamentares', painel_parlamentares_view),
    url(r'^sistema/painel/votacao', painel_votacao_view),
    url(r'^sistema/painel/json_presenca', json_presenca, name='json_presenca'),
    url(r'^sistema/painel/json_votacao', json_votacao, name='json_votacao'),
    url(r'^sistema/painel/cronometro',
        include(cronometro_painel_crud.urls)),
]
