from django.conf.urls import include, url

from .views import (controlador_painel, cronometro_painel_crud,
                    json_votacao, painel_mensagem_view,
                    painel_parlamentares_view, painel_view,
                    painel_votacao_view)

urlpatterns = [
    url(r'^(?P<pk>\d+)/painel$', painel_view, name="painel_principal"),
    url(r'^painel/(?P<pk>\d+)/json_votacao$', json_votacao, name='json_votacao'),
    url(r'^painel/controlador$', controlador_painel, name='painel_controlador'),
    url(r'^painel/mensagem$', painel_mensagem_view, name="painel_mensagem"),
    url(r'^painel/parlamentares$', painel_parlamentares_view, name='painel_parlamentares'),
    url(r'^painel/votacao$', painel_votacao_view, name='painel_votacao'),
    url(r'^painel/cronometro$', include(cronometro_painel_crud.urls)),
]
