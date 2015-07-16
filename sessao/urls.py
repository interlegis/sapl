from django.conf.urls import patterns, url

from sessao.views import SessaoListView, SessaoDetailView, SessaoUpdateView


urlpatterns = patterns(
    'comissoes.views',
    url(r'^$', SessaoListView.as_view(), name='sessao_list'),
    url(r'^(?P<pk>\d+)$', SessaoDetailView.as_view(), name='sessao_detail'),
    url(r'^(?P<pk>\d+)/edit$', SessaoUpdateView.as_view(), name='sessao_update'),
)
