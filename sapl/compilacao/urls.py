from django.conf.urls import include, url
from sapl.compilacao import views
from sapl.compilacao.views import (TipoDispositivoCrud, TipoNotaCrud,
                                   TipoPublicacaoCrud, TipoVideCrud,
                                   VeiculoPublicacaoCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_compilacao = [
    url(r'^$', views.TaListView.as_view(), name='ta_list'),
    url(r'^create$', views.TaCreateView.as_view(), name='ta_create'),
    url(r'^(?P<pk>[0-9]+)$', views.TaDetailView.as_view(), name='ta_detail'),
    url(r'^(?P<pk>[0-9]+)/edit$',
        views.TaUpdateView.as_view(), name='ta_edit'),
    url(r'^(?P<pk>[0-9]+)/delete$',
        views.TaDeleteView.as_view(), name='ta_delete'),


    url(r'^(?P<ta_id>[0-9]+)/text$',
        views.TextView.as_view(), name='ta_text'),

    url(r'^(?P<ta_id>[0-9]+)/text/vigencia/(?P<sign>.+)/$',
        views.TextView.as_view(), name='ta_vigencia'),

    url(r'^(?P<ta_id>[0-9]+)/text/edit',
        views.TextEditView.as_view(), name='ta_text_edit'),

    url(r'^(?P<ta_id>[0-9]+)/text/notifications',
        views.TextNotificacoesView.as_view(), name='ta_text_notificacoes'),

    url(r'^(?P<ta_id>[0-9]+)/text/(?P<dispositivo_id>[0-9]+)/$',
        views.DispositivoView.as_view(), name='dispositivo'),

    url(r'^(?P<ta_id>[0-9]+)/text/(?P<dispositivo_id>[0-9]+)/refresh',
        views.DispositivoDinamicEditView.as_view(),
        name='dispositivo_refresh'),

    url(r'^(?P<ta_id>[0-9]+)/text/(?P<pk>[0-9]+)/edit$',
        views.DispositivoEdicaoBasicaView.as_view(), name='dispositivo_edit'),

    url(r'^(?P<ta_id>[0-9]+)/text/(?P<pk>[0-9]+)/edit/vigencia',
        views.DispositivoEdicaoVigenciaView.as_view(),
        name='dispositivo_edit_vigencia'),

    url(r'^(?P<ta_id>[0-9]+)/text/(?P<pk>[0-9]+)/edit/alteracao',
        views.DispositivoEdicaoAlteracaoView.as_view(),
        name='dispositivo_edit_alteracao'),

    url(r'^(?P<ta_id>[0-9]+)/text/(?P<pk>[0-9]+)/edit/definidor_vigencia',
        views.DispositivoDefinidorVigenciaView.as_view(),
        name='dispositivo_edit_definidor_vigencia'),


    url(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/nota/create$',
        views.NotasCreateView.as_view(), name='nota_create'),

    url(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/nota/(?P<pk>[0-9]+)/edit$',
        views.NotasEditView.as_view(), name='nota_edit'),

    url(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/nota/(?P<pk>[0-9]+)/delete$',
        views.NotasDeleteView.as_view(), name='nota_delete'),

    url(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/vide/create$',
        views.VideCreateView.as_view(), name='vide_create'),

    url(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/vide/(?P<pk>[0-9]+)/edit$',
        views.VideEditView.as_view(), name='vide_edit'),

    url(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/vide/(?P<pk>[0-9]+)/delete$',
        views.VideDeleteView.as_view(), name='vide_delete'),

    url(r'^search_fragment_form$',
        views.DispositivoSearchFragmentFormView.as_view(),
        name='dispositivo_fragment_form'),

    url(r'^search_form$',
        views.DispositivoSearchModalView.as_view(),
        name='dispositivo_search_form'),


    url(r'^(?P<ta_id>[0-9]+)/publicacao$',
        views.PublicacaoListView.as_view(), name='ta_pub_list'),
    url(r'^(?P<ta_id>[0-9]+)/publicacao/create$',
        views.PublicacaoCreateView.as_view(), name='ta_pub_create'),
    url(r'^(?P<ta_id>[0-9]+)/publicacao/(?P<pk>[0-9]+)$',
        views.PublicacaoDetailView.as_view(), name='ta_pub_detail'),
    url(r'^(?P<ta_id>[0-9]+)/publicacao/(?P<pk>[0-9]+)/edit$',
        views.PublicacaoUpdateView.as_view(), name='ta_pub_edit'),
    url(r'^(?P<ta_id>[0-9]+)/publicacao/(?P<pk>[0-9]+)/delete$',
        views.PublicacaoDeleteView.as_view(), name='ta_pub_delete'),



]

urlpatterns = [
    url(r'^ta/', include(urlpatterns_compilacao)),

    url(r'^sistema/ta/config/tipo-nota/',
        include(TipoNotaCrud.get_urls())),
    url(r'^sistema/ta/config/tipo-vide/',
        include(TipoVideCrud.get_urls())),
    url(r'^sistema/ta/config/tipo-publicacao/',
        include(TipoPublicacaoCrud.get_urls())),
    url(r'^sistema/ta/config/veiculo-publicacao/',
        include(VeiculoPublicacaoCrud.get_urls())),
    url(r'^sistema/ta/config/tipo-dispositivo/',
        include(TipoDispositivoCrud.get_urls())),

    url(r'^sistema/ta/config/tipo-textoarticulado$',
    views.TipoTaListView.as_view(), name='tipo_ta_list'),
    url(r'^sistema/ta/config/tipo-textoarticulado/create$',
    views.TipoTaCreateView.as_view(), name='tipo_ta_create'),
    url(r'^sistema/ta/config/tipo-textoarticulado/(?P<pk>[0-9]+)$',
    views.TipoTaDetailView.as_view(), name='tipo_ta_detail'),
    url(r'^sistema/ta/config/tipo-textoarticulado/(?P<pk>[0-9]+)/edit$',
    views.TipoTaUpdateView.as_view(), name='tipo_ta_edit'),
    url(r'^sistema/ta/config/tipo-textoarticulado/(?P<pk>[0-9]+)/delete$',
    views.TipoTaDeleteView.as_view(), name='tipo_ta_delete'),
]
