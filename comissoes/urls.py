from django.conf.urls import url

from comissoes.views import (ComposicaoView, MateriasView, ReunioesView,
                             comissao_crud)

urlpatterns = comissao_crud.urlpatterns + [
    url(r'^(?P<pk>\d+)/composicao$',
        ComposicaoView.as_view(), name='composicao'),
    url(r'^(?P<pk>\d+)/materias$',
        MateriasView.as_view(), name='materias'),
    url(r'^(?P<pk>\d+)/reunioes$',
        ReunioesView.as_view(), name='reunioes'),
]
comissoes_urls = urlpatterns, comissao_crud.namespace, comissao_crud.namespace
