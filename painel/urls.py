from django.conf.urls import include, url

from . views import (json_view, painel_view, painel_parlamentares_view, painel_votacao_view)

urlpatterns = [
     url(r'^sistema/painel$', painel_view),
     url(r'^sistema/painel/parlamentares', painel_parlamentares_view),
     url(r'^sistema/painel/votacao', painel_votacao_view),
     url(r'^sistema/painel/json', json_view, name='json_view'),
]
