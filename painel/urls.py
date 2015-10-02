from django.conf.urls import include, url

from .views import (controlador_painel, cronometro_painel_crud,
                    json_votacao, painel_mensagem_view,
                    painel_parlamentares_view, painel_view,
                    painel_votacao_view)

urlpatterns = [
    url(r'^painel$', painel_view, name="painel"),
    url(r'^painel/controlador',
        controlador_painel, name='controlador_painel'),
    url(r'^painel/mensagem', painel_mensagem_view),
    url(r'^painel/parlamentares', painel_parlamentares_view),
    url(r'^painel/votacao', painel_votacao_view),
    url(r'^painel/(?P<pk>\d+)/json_votacao$', json_votacao, name='json_votacao'),
    url(r'^painel/cronometro',
        include(cronometro_painel_crud.urls)),
]
