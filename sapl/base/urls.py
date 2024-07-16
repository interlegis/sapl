import os

from django.contrib.auth import views
from django.contrib.auth.decorators import permission_required
from django.urls.conf import path, include
from django.views.generic.base import RedirectView, TemplateView

from sapl.base.views import (AutorCrud, ConfirmarEmailView, TipoAutorCrud, get_estatistica,
                             RecuperarSenhaEmailView, RecuperarSenhaFinalizadoView,
                             RecuperarSenhaConfirmaView, RecuperarSenhaCompletoView, IndexView, UserCrud)
from sapl.settings import MEDIA_URL, LOGOUT_REDIRECT_URL

from .apps import AppConfig
from .views import (LoginSapl, AlterarSenha, AppConfigCrud, CasaLegislativaCrud,
                    HelpTopicView, LogotipoView, PesquisarAuditLogView,
                    SaplSearchView,
                    ListarInconsistenciasView,
                    ListarProtocolosDuplicadosView, ListarProtocolosComMateriasView, ListarMatProtocoloInexistenteView,
                    ListarParlamentaresDuplicadosView, ListarFiliacoesSemDataFiliacaoView,
                    ListarMandatoSemDataInicioView, ListarParlMandatosIntersecaoView, ListarParlFiliacoesIntersecaoView,
                    ListarAutoresDuplicadosView, ListarBancadaComissaoAutorExternoView, ListarLegislaturaInfindavelView,
                    ListarAnexadasCiclicasView, ListarAnexadosCiclicosView, pesquisa_textual)


app_name = AppConfig.name

admin_user = [
    path(r'^sistema/usuario/', include(UserCrud.get_urls())),

]

alterar_senha = [
    path(r'^sistema/alterar-senha/$',
         AlterarSenha.as_view(),
         name='alterar_senha'),

]

recuperar_senha = [
    path(r'^recuperar-senha/email/$', RecuperarSenhaEmailView.as_view(),
         name='recuperar_senha_email'),
    path(r'^recuperar-senha/finalizado/$',
         RecuperarSenhaFinalizadoView.as_view(), name='recuperar_senha_finalizado'),
    path(r'^recuperar-senha/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', RecuperarSenhaConfirmaView.as_view(),
         name='recuperar_senha_confirma'),
    path(r'^recuperar-senha/completo/$',
         RecuperarSenhaCompletoView.as_view(), name='recuperar_senha_completo'),
]

urlpatterns = [
    path(r'^$', IndexView.as_view(template_name='index.html'), name='sapl_index'),

    path(r'^sistema/autor/tipo/', include(TipoAutorCrud.get_urls())),
    path(r'^sistema/autor/', include(AutorCrud.get_urls())),

    path(r'^sistema/ajuda/(?P<topic>\w+)$',
         HelpTopicView.as_view(), name='help_topic'),
    path(r'^sistema/ajuda/$', TemplateView.as_view(template_name='ajuda.html'),
         name='help'),
    path(r'^sistema/casa-legislativa/', include(CasaLegislativaCrud.get_urls()),
         name="casa_legislativa"),
    path(r'^sistema/app-config/', include(AppConfigCrud.get_urls())),

    path(r'^email/validate/(?P<uidb64>[0-9A-Za-z_\-]+)/'
         '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$',
         ConfirmarEmailView.as_view(), name='confirmar_email'),

    path(r'^sistema/inconsistencias/$',
         ListarInconsistenciasView.as_view(),
         name='lista_inconsistencias'),
    path(r'^sistema/inconsistencias/protocolos_duplicados$',
         ListarProtocolosDuplicadosView.as_view(),
         name='lista_protocolos_duplicados'),
    path(r'^sistema/inconsistencias/protocolos_com_materias$',
         ListarProtocolosComMateriasView.as_view(),
         name='lista_protocolos_com_materias'),
    path(r'^sistema/inconsistencias/materias_protocolo_inexistente$',
         ListarMatProtocoloInexistenteView.as_view(),
         name='lista_materias_protocolo_inexistente'),
    path(r'^sistema/inconsistencias/filiacoes_sem_data_filiacao$',
         ListarFiliacoesSemDataFiliacaoView.as_view(),
         name='lista_filiacoes_sem_data_filiacao'),
    path(r'^sistema/inconsistencias/mandato_sem_data_inicio',
         ListarMandatoSemDataInicioView.as_view(),
         name='lista_mandato_sem_data_inicio'),
    path(r'^sistema/inconsistencias/parlamentares_duplicados$',
         ListarParlamentaresDuplicadosView.as_view(),
         name='lista_parlamentares_duplicados'),
    path(r'^sistema/inconsistencias/parlamentares_mandatos_intersecao$',
         ListarParlMandatosIntersecaoView.as_view(),
         name='lista_parlamentares_mandatos_intersecao'),
    path(r'^sistema/inconsistencias/parlamentares_filiacoes_intersecao$',
         ListarParlFiliacoesIntersecaoView.as_view(),
         name='lista_parlamentares_filiacoes_intersecao'),
    path(r'^sistema/inconsistencias/autores_duplicados$',
         ListarAutoresDuplicadosView.as_view(),
         name='lista_autores_duplicados'),
    path(r'^sistema/inconsistencias/bancada_comissao_autor_externo$',
         ListarBancadaComissaoAutorExternoView.as_view(),
         name='lista_bancada_comissao_autor_externo'),
    path(r'^sistema/inconsistencias/legislatura_infindavel$',
         ListarLegislaturaInfindavelView.as_view(),
         name='lista_legislatura_infindavel'),
    path(r'sistema/inconsistencias/anexadas_ciclicas$',
         ListarAnexadasCiclicasView.as_view(),
         name='lista_anexadas_ciclicas'),
    path(r'sistema/inconsistencias/anexados_ciclicos$',
         ListarAnexadosCiclicosView.as_view(),
         name='lista_anexados_ciclicos'),

    path(r'^sistema/pesquisa-textual',
         pesquisa_textual,
         name='pesquisa_textual'),

    path(r'^sistema/estatisticas', get_estatistica),

    # todos os sublinks de sistema devem vir acima deste
    path(r'^sistema/$', permission_required('base.view_tabelas_auxiliares')
         (TemplateView.as_view(template_name='sistema.html')),
         name='sistema'),

    path(r'^login/$', LoginSapl.as_view(), name='login'),
    path(r'^logout/$', views.LogoutView.as_view(),
         {'next_page': LOGOUT_REDIRECT_URL}, name='logout'),

    path(r'^sistema/search/', SaplSearchView(), name='haystack_search'),

    path(r'^sistema/auditlog/$', PesquisarAuditLogView.as_view(),
         name='pesquisar_auditlog'),

    # Folhas XSLT e extras referenciadas por documentos migrados do sapl 2.5
    path(r'^(sapl/)?XSLT/HTML/(?P<path>.*)$', RedirectView.as_view(
        url=os.path.join(MEDIA_URL, 'sapl/public/XSLT/HTML/%(path)s'),
        permanent=False)),
    # url do logotipo usada em documentos migrados do sapl 2.5
    path(r'^(sapl/)?sapl_documentos/props_sapl/logo_casa',
         LogotipoView.as_view(), name='logotipo'),


] + recuperar_senha + alterar_senha + admin_user
