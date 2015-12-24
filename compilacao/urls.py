from django.conf.urls import include, url

from compilacao import views

urlpatterns_compilacao = [
    url(r'^$', views.TaListView.as_view(), name='ta_list'),
    url(r'^create$', views.TaCreateView.as_view(), name='ta_create'),
    url(r'^(?P<pk>[0-9]+)$', views.TaDetailView.as_view(), name='ta_detail'),
    url(r'^(?P<pk>[0-9]+)/edit$',
        views.TaUpdateView.as_view(), name='ta_edit'),
    url(r'^(?P<pk>[0-9]+)/delete$',
        views.TaDeleteView.as_view(), name='ta_delete'),
]

urlpatterns = [
    url(r'^ta/', include(urlpatterns_compilacao)),
]


"""
    url(r'^(?P<ta_id>[0-9]+)/compilacao$',
        views.CompilacaoView.as_view(), name='compilacao'),
    url(r'^(?P<ta_id>[0-9]+)/compilacao/(?P<dispositivo_id>[0-9]+)/$',
        views.DispositivoView.as_view(), name='dispositivo'),

    url(r'^(?P<ta_id>[0-9]+)/compilacao/vigencia/(?P<sign>.+)/$',
        views.CompilacaoView.as_view(), name='vigencia'),

    url(r'^(?P<ta_id>[0-9]+)/compilacao/edit',
        views.CompilacaoEditView.as_view(), name='comp_edit'),
    url(r'^(?P<ta_id>[0-9]+)/compilacao/(?P<dispositivo_id>[0-9]+)/refresh',
        views.DispositivoEditView.as_view(), name='dispositivo_edit'),

    url(r'^(?P<ta_id>[0-9]+)/compilacao/(?P<dispositivo_id>[0-9]+)/actions',
        views.ActionsEditView.as_view(), name='dispositivo_actions'),

    url(r'^(?P<ta_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/nota/create$',
        views.NotasCreateView.as_view(), name='nota_create'),

    url(r'^(?P<ta_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/nota/(?P<pk>[0-9]+)/edit$',
        views.NotasEditView.as_view(), name='nota_edit'),

    url(r'^(?P<ta_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/nota/(?P<pk>[0-9]+)/delete$',
        views.NotasDeleteView.as_view(), name='nota_delete'),

    url(r'^(?P<ta_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/vide/create$',
        views.VideCreateView.as_view(), name='vide_create'),

    url(r'^(?P<ta_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/vide/(?P<pk>[0-9]+)/edit$',
        views.VideEditView.as_view(), name='vide_edit'),

    url(r'^(?P<ta_id>[0-9]+)/compilacao/'
        '(?P<dispositivo_id>[0-9]+)/vide/(?P<pk>[0-9]+)/delete$',
        views.VideDeleteView.as_view(), name='vide_delete'),

    url(r'^(?P<ta_id>[0-9]+)/compilacao/search$',
        views.DispositivoSearchFragmentFormView.as_view(),
        name='search_dispositivo'),
"""
