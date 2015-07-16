from django.conf.urls import patterns, url

from sessao.views import SessaoPlenariaListView, SessaoPlenariaDetailView, SessaoPlenariaCreateView, SessaoPlenariaUpdateView


urlpatterns = patterns(
    'comissoes.views',
    url(r'^$', SessaoPlenariaListView.as_view(), name='sessaoplenaria_list'),
    url(r'^(?P<pk>\d+)$', SessaoPlenariaDetailView.as_view(), name='sessaoplenaria_detail'),
    url(r'^add$', SessaoPlenariaCreateView.as_view(), name='sessaoplenaria_update'),
    url(r'^(?P<pk>\d+)/edit$', SessaoPlenariaUpdateView.as_view(), name='sessaoplenaria_update'),
)
