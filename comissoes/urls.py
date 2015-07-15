from django.conf.urls import patterns, url

from comissoes.views import (ListaComissoes,
                             CriarComissao)

urlpatterns = patterns(
    'comissoes.views',
    url(r'^$', ListaComissoes.as_view(), name='ListaComissoes'),
    #url(r'^incluir$', CriarComissao.as_view(), name='CriarComissao'),
)
