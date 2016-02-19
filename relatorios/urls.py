from django.conf.urls import url

from .views import (relatorio_capa_processo,
                    relatorio_documento_administrativo, relatorio_espelho,
                    relatorio_etiqueta_protocolo, relatorio_materia,
                    relatorio_ordem_dia, relatorio_pauta_sessao,
                    relatorio_protocolo, relatorio_sessao_plenaria)

urlpatterns = [
    url(r'^relatorios/materia$', relatorio_materia, name='relatorio_materia'),
    url(r'^relatorios/capa_processo$',
        relatorio_capa_processo, name='relatorio_capa_processo'),
    url(r'^relatorios/ordem_dia$', relatorio_ordem_dia,
        name='relatorio_ordem_dia'),
    url(r'^relatorios/relatorio_documento_administrativo$',
        relatorio_documento_administrativo,
        name='relatorio_documento_administrativo'),
    url(r'^relatorios/espelho$', relatorio_espelho,
        name='relatorio_espelho'),
    url(r'^relatorios/(?P<pk>\d+)/sessao_plenaria$',
        relatorio_sessao_plenaria, name='relatorio_sessao_plenaria'),
    url(r'^relatorios/protocolo$',
        relatorio_protocolo, name='relatorio_protocolo'),
    url(r'^relatorios/(?P<nro>\d+)/(?P<ano>\d+)/etiqueta_protocolo$',
        relatorio_etiqueta_protocolo, name='relatorio_etiqueta_protocolo'),
    url(r'^relatorios/pauta_sessao$',
        relatorio_pauta_sessao, name='relatorio_pauta_sessao'),
]
