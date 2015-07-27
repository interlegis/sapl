from django.conf.urls import patterns, url

from sessao.views import (SessaoPlenariaCreateView, SessaoPlenariaDetailView,
                          SessaoPlenariaListView, SessaoPlenariaUpdateView)

urlpatterns = patterns(
    'sessao.views',
    url(r'^$', SessaoPlenariaListView.as_view(), name='sessao_list'),
    url(r'^(?P<pk>\d+)$', SessaoPlenariaDetailView.as_view(),
        name='sessao_detail'),
    url(r'^create$', SessaoPlenariaCreateView.as_view(),
        name='sessao_create'),
    url(r'^(?P<pk>\d+)/edit$', SessaoPlenariaUpdateView.as_view(),
        name='sessao_update'),
)
