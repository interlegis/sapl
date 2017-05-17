from .views import (
    RedirecionaComissao,
    RedirecionaMateriaLegislativaDetail,
    RedirecionaMateriaLegislativaList,
    RedirecionaParlamentar,
    RedirecionaPautaSessao,
    RedirecionaRelatoriosList,
    RedirecionaRelatoriosMateriasEmTramitacaoList,
    RedirecionaSessaoPlenaria,
    RedirecionaSAPLIndex)
from django.conf.urls import url


from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    url(r'^default_index_html$',
        RedirecionaSAPLIndex.as_view(),
        name='redireciona_sapl_index'),
    url(r'^consultas/parlamentar/parlamentar_',
        RedirecionaParlamentar.as_view(),
        name='redireciona_parlamentar'),
    url(r'^consultas/comissao/comissao_',
        RedirecionaComissao.as_view(),
        name='redireciona_comissao'),
    url(r'^consultas/pauta_sessao/pauta_sessao_',
        RedirecionaPautaSessao.as_view(),
        name='redireciona_pauta_sessao_'),
    url(r'^consultas/sessao_plenaria/',
        RedirecionaSessaoPlenaria.as_view(),
        name='redireciona_sessao_plenaria_'),
    url(r'^relatorios_administrativos/relatorios_administrativos_index_html$',
        RedirecionaRelatoriosList.as_view(),
        name='redireciona_relatorios_list'),
    url(r'^relatorios_administrativos/tramitacaoMaterias/tramitacaoMaterias',
        RedirecionaRelatoriosMateriasEmTramitacaoList.as_view(),
        name='redireciona_relatorio_materia_por_tramitacao'),
    url(r'^relatorios_administrativos/tramitacaoMaterias/materia_mostrar_proc$',
        RedirecionaMateriaLegislativaDetail.as_view(),
        name='redireciona_materialegislativa_detail'),
    url(r'^generico/materia_pesquisar_',
        RedirecionaMateriaLegislativaList.as_view(),
        name='redireciona_materialegislativa_list'),
]
