from django.conf.urls import url

from comissoes.views import (
    comissao_crud, ComposicaoListView, MateriasListView, ReunioesListView)


urlpatterns = comissao_crud.urlpatterns + [
    url(r'^(?P<pk>\d+)/composicao$',
        ComposicaoListView.as_view(), name='composicao'),
    url(r'^(?P<pk>\d+)/materias$',
        MateriasListView.as_view(), name='materias'),
    url(r'^(?P<pk>\d+)/reunioes$',
        ReunioesListView.as_view(), name='reunioes'),
]
comissoes_urls = urlpatterns, comissao_crud.namespace, comissao_crud.namespace
