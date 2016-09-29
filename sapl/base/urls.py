from django.conf.urls import include, url
from django.contrib.auth import views
from django.contrib.auth.decorators import permission_required
from django.views.generic.base import TemplateView

from .apps import AppConfig
from .forms import LoginForm
from .views import (AppConfigCrud, CasaLegislativaCrud, HelpView,
                    RelatorioAtasView, RelatorioHistoricoTramitacaoView,
                    RelatorioMateriasPorAnoAutorTipoView,
                    RelatorioMateriasPorAutorView,
                    RelatorioMateriasTramitacaoView,
                    RelatorioPresencaSessaoView)


app_name = AppConfig.name


urlpatterns = [
    url(r'^sistema/', permission_required('base.view_tabelas_auxiliares')
        (TemplateView.as_view(template_name='sistema.html'))),

    url(r'^ajuda/', TemplateView.as_view(template_name='ajuda.html')),
    url(r'^relatorios/', TemplateView.as_view(
        template_name='base/relatorios_list.html')),
    url(r'^ajuda/(?P<topic>\w+)$', HelpView.as_view(), name='help_topic'),
    url(r'^ajuda/', TemplateView.as_view(template_name='ajuda/index.html'),
        name='help_base'),
    url(r'^casa-legislativa/', include(CasaLegislativaCrud.get_urls()),
        name="casa_legislativa"),
    url(r'^app-config/', include(AppConfigCrud.get_urls())),

    url(r'^login/$', views.login, {
        'template_name': 'base/login.html', 'authentication_form': LoginForm},
        name='login'),
    url(r'^logout/$', views.logout, {'next_page': '/login'}, name='logout'),

    url(r'^relatorios/materia-por-autor$',
        RelatorioMateriasPorAutorView.as_view(), name='materia_por_autor'),
    url(r'^relatorios/materia-por-ano-autor-tipo$',
        RelatorioMateriasPorAnoAutorTipoView.as_view(),
        name='materia_por_ano_autor_tipo'),
    url(r'^relatorios/materia-por-tramitacao$',
        RelatorioMateriasTramitacaoView.as_view(),
        name='materia_por_tramitacao'),
    url(r'^relatorios/historico-tramitacoes$',
        RelatorioHistoricoTramitacaoView.as_view(),
        name='historico_tramitacoes'),
    url(r'^relatorios/presenca$',
        RelatorioPresencaSessaoView.as_view(),
        name='presenca_sessao'),
    url(r'^relatorios/atas$',
        RelatorioAtasView.as_view(),
        name='atas'),

]
