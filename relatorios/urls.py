from django.conf.urls import url

from .views import relatorio_materia, relatorio_processo

urlpatterns = [
    url(r'^relatorios/materia$', relatorio_materia, name='relatorio_materia'),
    url(r'^relatorios/cap_processo$',
        relatorio_processo, name='relatorio_cap_processo'),
]
