from django.conf.urls import url
from django.urls import path

from .apps import AppConfig
from .views import (cronometro_painel, painel_view,
                    switch_painel, verifica_painel, votante_status, votante_view,
                    vote_controller, cancel_voting, close_voting, votos_status)

app_name = AppConfig.name

urlpatterns = [

    ## Votacao - FRONTEND (Django/VueJS)
    path("painel/<int:sessao_id>", painel_view, name='painel_principal'),
    path("painel/voto-individual", votante_view, name='voto_individual'),

    ## Votacao - API
    path("voto-individual/status", votante_status, name='voto_individual_status'),    
    path("painel/switch-painel", switch_painel, name="switch_painel"),
    path("painel/verifica-painel", verifica_painel, name="verifica_painel"),    
    path("painel/cronometro", cronometro_painel, name='cronometro_painel'),    
    path("painel/controller/<int:controller_id>/vote",
         vote_controller, name='vote_controller'),
    path("painel/controller/<int:controller_id>/cancel",
         cancel_voting, name='cancel_voting'),
    path("painel/controller/<int:controller_id>/close",
         close_voting, name='close_voting'),
    path("painel/controller/<int:controller_id>/votos-status",
         votos_status, name='votos_status'),
]
