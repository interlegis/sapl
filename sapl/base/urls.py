from django.conf.urls import include, url
from django.contrib.auth import views
from django.contrib.auth.decorators import permission_required
from django.views.generic.base import TemplateView

from sapl.base.views import AutorCrud, TipoAutorCrud

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
<<<<<<< 6123d2617726dd220c02c2bb3b3c27ed4b136df1
=======
    url(r'^sistema/autor/tipo/', include(TipoAutorCrud.get_urls())),
    url(r'^sistema/autor/', include(AutorCrud.get_urls())),

>>>>>>> Ref Autor, TipoAutor, cria app api DRF
    url(r'^sistema/ajuda/', TemplateView.as_view(template_name='ajuda.html')),
    url(r'^sistema/ajuda/(?P<topic>\w+)$',
        HelpView.as_view(), name='help_topic'),
    url(r'^sistema/ajuda/', TemplateView.as_view(template_name='ajuda/index.html'),
        name='help_base'),
    url(r'^sistema/casa-legislativa/', include(CasaLegislativaCrud.get_urls()),
        name="casa_legislativa"),
    url(r'^sistema/app-config/', include(AppConfigCrud.get_urls())),

    # TODO mover estas telas para a app 'relatorios'
    url(r'^sistema/relatorios/$', TemplateView.as_view(
        template_name='base/relatorios_list.html')),
    url(r'^sistema/relatorios/materia-por-autor$',
        RelatorioMateriasPorAutorView.as_view(), name='materia_por_autor'),
    url(r'^sistema/relatorios/materia-por-ano-autor-tipo$',
        RelatorioMateriasPorAnoAutorTipoView.as_view(),
        name='materia_por_ano_autor_tipo'),
    url(r'^sistema/relatorios/materia-por-tramitacao$',
        RelatorioMateriasTramitacaoView.as_view(),
        name='materia_por_tramitacao'),
    url(r'^sistema/relatorios/historico-tramitacoes$',
        RelatorioHistoricoTramitacaoView.as_view(),
        name='historico_tramitacoes'),
    url(r'^sistema/relatorios/presenca$',
        RelatorioPresencaSessaoView.as_view(),
        name='presenca_sessao'),
    url(r'^sistema/relatorios/atas$',
        RelatorioAtasView.as_view(),
        name='atas'),

<<<<<<< 6123d2617726dd220c02c2bb3b3c27ed4b136df1
=======

    # todos os sublink s de sistema devem vir acima deste
>>>>>>> Ref Autor, TipoAutor, cria app api DRF
    url(r'^sistema/', permission_required('base.view_tabelas_auxiliares')
        (TemplateView.as_view(template_name='sistema.html'))),


<<<<<<< 6123d2617726dd220c02c2bb3b3c27ed4b136df1
=======
    url(r'^login/$', views.login, {
        'template_name': 'base/login.html', 'authentication_form': LoginForm},
        name='login'),
    url(r'^logout/$', views.logout, {'next_page': '/login'}, name='logout'),

>>>>>>> Ref Autor, TipoAutor, cria app api DRF
]
