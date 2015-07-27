from django.conf.urls import url

from sessao.views import ExpedienteView, sessao_crud

urlpatterns = sessao_crud.urlpatterns + [
    url(r'^(?P<pk>\d+)/expediente$',
        ExpedienteView.as_view(), name='expediente'),
]
sessao_urls = urlpatterns, sessao_crud.namespace, sessao_crud.namespace
