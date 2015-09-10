from django.conf.urls import include, url
from sessao.views import (ExpedienteView, OradorExpedienteView, PainelView,
                          PresencaOrdemDiaView, PresencaView, sessao_crud,
                          tipo_expediente_crud, tipo_resultado_votacao_crud,
                          tipo_sessao_crud)

urlpatterns_sessao = sessao_crud.urlpatterns + [
    url(r'^(?P<pk>\d+)/expediente$',
        ExpedienteView.as_view(), name='expediente'),
    url(r'^(?P<pk>\d+)/presenca$',
        PresencaView.as_view(), name='presenca'),
    url(r'^(?P<pk>\d+)/painel$',
        PainelView.as_view(), name='painel'),
    url(r'^(?P<pk>\d+)/presencaordemdia$',
        PresencaOrdemDiaView.as_view(),
        name='presencaordemdia'),
    url(r'^(?P<pk>\d+)/oradorexpediente$',
        OradorExpedienteView.as_view(), name='oradorexpediente'),
]
sessao_urls = urlpatterns_sessao, sessao_crud.namespace, sessao_crud.namespace

urlpatterns = [
    url(r'^sessao/', include(urlpatterns_sessao,
                             sessao_crud.namespace, sessao_crud.namespace)),
    url(r'^sistema/sessao-plenaria/tipo/', include(tipo_sessao_crud.urls)),
    url(r'^sistema/sessao-plenaria/tipo-resultado-votacao/',
        include(tipo_resultado_votacao_crud.urls)),
    url(r'^sistema/sessao-plenaria/tipo-expediente/',
        include(tipo_expediente_crud.urls)),
]
