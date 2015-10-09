from django.conf.urls import url, include
from django.contrib.auth.decorators import permission_required

from compilacao import views
from compilacao.views import (tipo_nota_crud, tipo_vide_crud,
                              tipo_publicacao_crud, veiculo_publicacao_crud,
                              tipo_dispositivo_crud)


urlpatterns_compilacao = [
    url(r'^(?P<norma_id>[0-9]+)/compilacao/$',
        views.CompilacaoView.as_view(), name='compilacao'),
    url(r'^(?P<norma_id>[0-9]+)/compilacao/(?P<dispositivo_id>[0-9]+)/$',
        views.DispositivoView.as_view(), name='dispositivo'),

    url(r'^(?P<norma_id>[0-9]+)/compilacao/vigencia/(?P<sign>.+)/$',
        views.CompilacaoView.as_view(), name='vigencia'),

    url(r'^(?P<norma_id>[0-9]+)/compilacao/edit',
        views.CompilacaoEditView.as_view(), name='comp_edit'),
    url(r'^(?P<norma_id>[0-9]+)/compilacao/(?P<dispositivo_id>[0-9]+)/refresh',
        views.DispositivoEditView.as_view(), name='dispositivo_edit'),

    url(r'^(?P<norma_id>[0-9]+)/compilacao/(?P<dispositivo_id>[0-9]+)/actions',
        views.ActionsEditView.as_view(), name='dispositivo_actions'),

]

urlpatterns = [
    url(r'^norma/', include(urlpatterns_compilacao)),

    url(r'^sistema/compilacao/tipo-nota/',
        include(tipo_nota_crud.urls)),
    url(r'^sistema/compilacao/tipo-vide/',
        include(tipo_vide_crud.urls)),
    url(r'^sistema/compilacao/tipo-publicacao/',
        include(tipo_publicacao_crud.urls)),
    url(r'^sistema/compilacao/tipo-dispositivo/',
        include(tipo_dispositivo_crud.urls)),
    url(r'^sistema/compilacao/veiculo-publicacao/',
        include(veiculo_publicacao_crud.urls)),
]
