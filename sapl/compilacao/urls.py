from django.urls import include, path, re_path

from sapl.compilacao import views
from sapl.compilacao.views import (TipoDispositivoCrud, TipoNotaCrud,
                                   TipoPublicacaoCrud, TipoVideCrud,
                                   VeiculoPublicacaoCrud,
                                   TipoTextoArticuladoCrud)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_compilacao = [
    path('', views.TaListView.as_view(), name='ta_list'),
    path('create', views.TaCreateView.as_view(), name='ta_create'),
    path('<int:pk>', views.TaDetailView.as_view(), name='ta_detail'),
    path('<int:pk>/edit',
        views.TaUpdateView.as_view(), name='ta_edit'),
    path('<int:pk>/delete',
        views.TaDeleteView.as_view(), name='ta_delete'),


    path('<int:ta_id>/text',
        views.TextView.as_view(), name='ta_text'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/vigencia/(?P<sign>.*:[A-Za-z0-9_-]+)/$',
        views.TextView.as_view(), name='ta_vigencia'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/edit',
        views.TextEditView.as_view(), name='ta_text_edit'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/notifications',
        views.TextNotificacoesView.as_view(), name='ta_text_notificacoes'),

    path('<int:ta_id>/text/<int:dispositivo_id>/',
        views.DispositivoView.as_view(), name='dispositivo'),

    re_path(r'^(?P<ta_id>[0-9]+)/text/(?P<dispositivo_id>[0-9]+)/refresh',
        views.DispositivoDinamicEditView.as_view(),
        name='dispositivo_refresh'),

    path('<int:ta_id>/text/<int:pk>/edit',
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


    path('<int:ta_id>/text/<int:dispositivo_id>/nota/create',
        views.NotasCreateView.as_view(), name='nota_create'),

    path('<int:ta_id>/text/<int:dispositivo_id>/nota/<int:pk>/edit',
        views.NotasEditView.as_view(), name='nota_edit'),

    path('<int:ta_id>/text/<int:dispositivo_id>/nota/<int:pk>/delete',
        views.NotasDeleteView.as_view(), name='nota_delete'),

    path('<int:ta_id>/text/<int:dispositivo_id>/vide/create',
        views.VideCreateView.as_view(), name='vide_create'),

    path('<int:ta_id>/text/<int:dispositivo_id>/vide/<int:pk>/edit',
        views.VideEditView.as_view(), name='vide_edit'),

    path('<int:ta_id>/text/<int:dispositivo_id>/vide/<int:pk>/delete',
        views.VideDeleteView.as_view(), name='vide_delete'),

    path('search_fragment_form',
        views.DispositivoSearchFragmentFormView.as_view(),
        name='dispositivo_fragment_form'),

    path('search_form',
        views.DispositivoSearchModalView.as_view(),
        name='dispositivo_search_form'),


    path('<int:ta_id>/publicacao',
        views.PublicacaoListView.as_view(), name='ta_pub_list'),
    path('<int:ta_id>/publicacao/create',
        views.PublicacaoCreateView.as_view(), name='ta_pub_create'),
    path('<int:ta_id>/publicacao/<int:pk>',
        views.PublicacaoDetailView.as_view(), name='ta_pub_detail'),
    path('<int:ta_id>/publicacao/<int:pk>/edit',
        views.PublicacaoUpdateView.as_view(), name='ta_pub_edit'),
    path('<int:ta_id>/publicacao/<int:pk>/delete',
        views.PublicacaoDeleteView.as_view(), name='ta_pub_delete'),



]

urlpatterns = [
    path('ta/', include(urlpatterns_compilacao)),

    path('sistema/ta/config/tipo-nota/',
        include(TipoNotaCrud.get_urls())),
    path('sistema/ta/config/tipo-vide/',
        include(TipoVideCrud.get_urls())),
    path('sistema/ta/config/tipo-publicacao/',
        include(TipoPublicacaoCrud.get_urls())),
    path('sistema/ta/config/veiculo-publicacao/',
        include(VeiculoPublicacaoCrud.get_urls())),
    path('sistema/ta/config/tipo/',
        include(TipoTextoArticuladoCrud.get_urls())),
    path('sistema/ta/config/tipodispositivo/',
        include(TipoDispositivoCrud.get_urls())),



]
