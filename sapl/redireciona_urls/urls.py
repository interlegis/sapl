from .views import (
    RedirecionaComissaoDetail,
    RedirecionaComissaoList,
    RedirecionaParlamentarDetail,
    RedirecionaParlamentarList,
    RedirecionaPautaSessaoDetail,
    RedirecionaPautaSessaoList,
    RedirecionaSessaoPlenariaList,
    RedirecionaSAPLIndex,
    RedirecionaSessaoPlenariaDetail)
from django.conf.urls import url


from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^default_index_html$',
        RedirecionaSAPLIndex.as_view(),
        name='redireciona_sapl_index'),
    url(r'^consultas/parlamentar/parlamentar_mostrar_proc$',
        RedirecionaParlamentarDetail.as_view(),
        name='redireciona_parlamentar_detail'),
    url(r'^consultas/parlamentar/parlamentar_index_html$',
        RedirecionaParlamentarList.as_view(),
        name='redireciona_parlamentar_list'),
    url(r'^consultas/comissao/comissao_index_html$',
        RedirecionaComissaoList.as_view(),
        name='redireciona_comissao_list'),
    url(r'^consultas/comissao/comissao_mostrar_proc$',
        RedirecionaComissaoDetail.as_view(),
        name='redireciona_comissao_detail'),
    url(r'^consultas/pauta_sessao/pauta_sessao_plen_mostrar_proc$',
        RedirecionaPautaSessaoDetail.as_view(),
        name='redireciona_pauta_sessao_detail'),
    url(r'^consultas/pauta_sessao/pauta_sessao_index_html$',
        RedirecionaPautaSessaoList.as_view(),
        name='redireciona_pauta_sessao_list'),
    url(r'^consultas/sessao_plenaria/sessao_plenaria_index_html$',
        RedirecionaSessaoPlenariaList.as_view(),
        name='redireciona_sessao_plenaria_list'),
    url(r'^consultas/sessao_plenaria/agenda_sessao_plen_mostrar_proc$',
        RedirecionaSessaoPlenariaDetail.as_view(),
        name='redireciona_sessao_plenaria_detail'),
]
