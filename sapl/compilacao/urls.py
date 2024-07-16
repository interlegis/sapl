from django.urls.conf import re_path, include

from sapl.compilacao import views
from sapl.compilacao.views import (TipoDispositivoCrud, TipoNotaCrud,
                                   TipoPublicacaoCrud, TipoVideCrud,
                                   VeiculoPublicacaoCrud,
                                   TipoTextoArticuladoCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_compilacao = [
    re_path(r'^$', views.TaListView.as_view(), name='ta_list'),
    re_path(r'^create$', views.TaCreateView.as_view(), name='ta_create'),
    re_path(r'^(?P<pk>[0-9]+)$', views.TaDetailView.as_view(), name='ta_detail'),
    re_path(r'^(?P<pk>[0-9]+)/edit$',
        views.TaUpdateView.as_view(), name='ta_edit'),
    re_path(r'^(?P<pk>[0-9]+)/delete$',
        views.TaDeleteView.as_view(), name='ta_delete'),


    re_path(r'^(?P<ta_id>[0-9]+)/text$',
        views.TextView.as_view(), name='ta_text'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/vigencia/(?P<sign>.+)/$',
        views.TextView.as_view(), name='ta_vigencia'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/edit',
        views.TextEditView.as_view(), name='ta_text_edit'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/notifications',
        views.TextNotificacoesView.as_view(), name='ta_text_notificacoes'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/(?P<dispositivo_id>[0-9]+)/$',
        views.DispositivoView.as_view(), name='dispositivo'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/(?P<dispositivo_id>[0-9]+)/refresh',
        views.DispositivoDinamicEditView.as_view(),
        name='dispositivo_refresh'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/(?P<pk>[0-9]+)/edit$',
        views.DispositivoEdicaoBasicaView.as_view(), name='dispositivo_edit'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/(?P<pk>[0-9]+)/edit/vigencia',
        views.DispositivoEdicaoVigenciaView.as_view(),
        name='dispositivo_edit_vigencia'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/(?P<pk>[0-9]+)/edit/alteracao',
        views.DispositivoEdicaoAlteracaoView.as_view(),
        name='dispositivo_edit_alteracao'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/(?P<pk>[0-9]+)/edit/definidor_vigencia',
        views.DispositivoDefinidorVigenciaView.as_view(),
        name='dispositivo_edit_definidor_vigencia'),


    re_path(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/nota/create$',
        views.NotasCreateView.as_view(), name='nota_create'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/nota/(?P<pk>[0-9]+)/edit$',
        views.NotasEditView.as_view(), name='nota_edit'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/nota/(?P<pk>[0-9]+)/delete$',
        views.NotasDeleteView.as_view(), name='nota_delete'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/vide/create$',
        views.VideCreateView.as_view(), name='vide_create'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/vide/(?P<pk>[0-9]+)/edit$',
        views.VideEditView.as_view(), name='vide_edit'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/'
        '(?P<dispositivo_id>[0-9]+)/vide/(?P<pk>[0-9]+)/delete$',
        views.VideDeleteView.as_view(), name='vide_delete'),

    re_path(r'^search_fragment_form$',
        views.DispositivoSearchFragmentFormView.as_view(),
        name='dispositivo_fragment_form'),

    re_path(r'^search_form$',
        views.DispositivoSearchModalView.as_view(),
        name='dispositivo_search_form'),


    re_path(r'^(?P<ta_id>[0-9]+)/publicacao$',
        views.PublicacaoListView.as_view(), name='ta_pub_list'),
    re_path(r'^(?P<ta_id>[0-9]+)/publicacao/create$',
        views.PublicacaoCreateView.as_view(), name='ta_pub_create'),
    re_path(r'^(?P<ta_id>[0-9]+)/publicacao/(?P<pk>[0-9]+)$',
        views.PublicacaoDetailView.as_view(), name='ta_pub_detail'),
    re_path(r'^(?P<ta_id>[0-9]+)/publicacao/(?P<pk>[0-9]+)/edit$',
        views.PublicacaoUpdateView.as_view(), name='ta_pub_edit'),
    re_path(r'^(?P<ta_id>[0-9]+)/publicacao/(?P<pk>[0-9]+)/delete$',
        views.PublicacaoDeleteView.as_view(), name='ta_pub_delete'),



]

urlpatterns = [
    re_path(r'^ta/', include(urlpatterns_compilacao)),

    re_path(r'^sistema/ta/config/tipo-nota/',
        include(TipoNotaCrud.get_urls())),
    re_path(r'^sistema/ta/config/tipo-vide/',
        include(TipoVideCrud.get_urls())),
    re_path(r'^sistema/ta/config/tipo-publicacao/',
        include(TipoPublicacaoCrud.get_urls())),
    re_path(r'^sistema/ta/config/veiculo-publicacao/',
        include(VeiculoPublicacaoCrud.get_urls())),
    re_path(r'^sistema/ta/config/tipo/',
        include(TipoTextoArticuladoCrud.get_urls())),
    re_path(r'^sistema/ta/config/tipodispositivo/',
        include(TipoDispositivoCrud.get_urls())),



]
