from django.conf.urls import include, url

from compilacao import views
from compilacao.views import (perfil_estr_txt_norm, tipo_dispositivo_crud,
                              tipo_nota_crud, tipo_publicacao_crud,
                              tipo_vide_crud, veiculo_publicacao_crud)

urlpatterns_compilacao = [
    url(r'^(?P<norma_id>[0-9]+)/compilacao$',
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

    url(r'^(?P<norma_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/nota/create$',
        views.NotasCreateView.as_view(), name='nota_create'),

    url(r'^(?P<norma_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/nota/(?P<pk>[0-9]+)/edit$',
        views.NotasEditView.as_view(), name='nota_edit'),

    url(r'^(?P<norma_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/nota/(?P<pk>[0-9]+)/delete$',
        views.NotasDeleteView.as_view(), name='nota_delete'),

    url(r'^(?P<norma_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/vide/create$',
        views.VideCreateView.as_view(), name='vide_create'),

    url(r'^(?P<norma_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/vide/(?P<pk>[0-9]+)/edit$',
        views.VideEditView.as_view(), name='vide_edit'),

    url(r'^(?P<norma_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/vide/(?P<pk>[0-9]+)/delete$',
        views.VideDeleteView.as_view(), name='vide_delete'),

    url(r'^(?P<norma_id>[0-9]+)/compilacao/search$',
        views.DispositivoSearchFragmentFormView.as_view(),
        name='search_dispositivo'),

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
    url(r'^sistema/compilacao/perfil-estrutural-textos-normativos/',
        include(perfil_estr_txt_norm.urls)),
]
