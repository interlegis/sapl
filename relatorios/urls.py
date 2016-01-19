from django.conf.urls import url

from .views import (relatorio_documento_administrativo, relatorio_materia,
                    relatorio_ordem_dia, relatorio_processo, relatorio_espelho)

urlpatterns = [
    url(r'^relatorios/materia$', relatorio_materia, name='relatorio_materia'),
    url(r'^relatorios/cap_processo$',
        relatorio_processo, name='relatorio_cap_processo'),
    url(r'^relatorios/ordem_dia$', relatorio_ordem_dia,
        name='relatorio_ordem_dia'),
    url(r'^relatorios/relatorio_documento_administrativo$',
        relatorio_documento_administrativo,
        name='relatorio_documento_administrativo'),
    url(r'^relatorios/espelho$', relatorio_espelho,
        name='relatorio_espelho'),

]
