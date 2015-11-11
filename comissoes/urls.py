from django.conf.urls import include, url

from comissoes.views import (ComposicaoView, MateriasView, ReunioesView,
                             cargo_crud, comissao_crud,
                             ComissaoParlamentarIncluirView,
                             periodo_composicao_crud, tipo_comissao_crud)

comissao_url_patterns = comissao_crud.urlpatterns + [
    url(r'^(?P<pk>\d+)/composicao$',
        ComposicaoView.as_view(), name='composicao'),
    url(r'^(?P<pk>\d+)/composicao/parlamentar',
        ComissaoParlamentarIncluirView.as_view(), name='comissao_parlamentar'),
    url(r'^(?P<pk>\d+)/materias$',
        MateriasView.as_view(), name='materias'),
    url(r'^(?P<pk>\d+)/reunioes$',
        ReunioesView.as_view(), name='reunioes'),
]

urlpatterns = [
    url(r'^comissoes/', include(comissao_url_patterns,
                                comissao_crud.namespace,
                                comissao_crud.namespace)),

    url(r'^sistema/comissoes/cargo/', include(cargo_crud.urls)),
    url(r'^sistema/comissoes/periodo-composicao/',
        include(periodo_composicao_crud.urls)),
    url(r'^sistema/comissoes/tipo/', include(tipo_comissao_crud.urls)),
]
