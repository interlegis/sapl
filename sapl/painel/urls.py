from django.conf.urls import url
from django.urls import path

from .apps import AppConfig
from .views import (cronometro_painel, painel_view,
                    switch_painel, verifica_painel, votante_status, votante_view,
                    votante_view_v2, websocket_view, vote_controller,
                    cancel_voting, close_voting, votos_status)

app_name = AppConfig.name

urlpatterns = [
    url(r'^painel-principal/(?P<pk>\d+)$', painel_view,
        name="painel_principal"),
    url(r'^painel/switch-painel$', switch_painel,
        name="switch_painel"),
    url(r'^painel/verifica-painel$', verifica_painel,
        name="verifica_painel"),
    url(r'^painel/cronometro$', cronometro_painel, name='cronometro_painel'),
    # url(r'^painel/cronometro$', include(CronometroPainelCrud.get_urls())),

    url(r'^voto-individual/$', votante_view,
        name='voto_individual'),
    url(r'^voto-individual/status$', votante_status,
        name='voto_individual_status'),
    url(r'^voto-individual/v2$', votante_view_v2,
        name='voto_individual_v2'),

    path("v2/painel/<int:controller_id>", websocket_view, name='painel_websocket'),
    path("v2/painel/controller/<int:controller_id>/vote",
         vote_controller, name='vote_controller'),
    path("v2/painel/controller/<int:controller_id>/cancel",
         cancel_voting, name='cancel_voting'),
    path("v2/painel/controller/<int:controller_id>/close",
         close_voting, name='close_voting'),
    path("v2/painel/controller/<int:controller_id>/votos-status",
         votos_status, name='votos_status'),
]
