from django.conf.urls import patterns, url

from comissoes.views import ListaComissoes


urlpatterns = patterns(
    'comissoes.views',
    url(r'^$', ListaComissoes.as_view(), name='ListaComissoes'),
)
