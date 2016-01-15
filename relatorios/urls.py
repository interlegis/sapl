from django.conf.urls import url

from .views import relatorio_materia

urlpatterns = [
    url(r'^relatorios/materia$', relatorio_materia, name='relatorio_materia'),
]
