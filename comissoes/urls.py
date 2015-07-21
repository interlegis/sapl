from django.conf.urls import url

from comissoes.views import (
    ComissaoListView, ComissaoDetailView, ComissaoUpdateView)


urlpatterns = [
    url(r'^$', ComissaoListView.as_view(), name='comissao_list'),
    url(r'^(?P<pk>\d+)$', ComissaoDetailView.as_view(),
        name='comissao_detail'),
    url(r'^(?P<pk>\d+)/edit$', ComissaoUpdateView.as_view(),
        name='comissao_update'),
]
