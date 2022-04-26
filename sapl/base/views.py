from collections import OrderedDict
import collections
import datetime
import itertools
import logging
import os

from django.contrib import messages
from django.contrib.auth import get_user_model, views
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView,
                                       PasswordResetDoneView)
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.db import connection
from django.db.models import Count, Q, Max, F
from django.forms.utils import ErrorList
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (FormView, ListView)
from django.views.generic.base import RedirectView, TemplateView
from django_filters.views import FilterView
from haystack.query import SearchQuerySet
from haystack.views import SearchView

from ratelimit.decorators import ratelimit
from sapl import settings
from sapl.audiencia.models import AudienciaPublica, TipoAudienciaPublica
from sapl.base.forms import (AutorForm, TipoAutorForm, AutorFilterSet, RecuperarSenhaForm,
                             NovaSenhaForm, UserAdminForm,
                             OperadorAutorForm, LoginForm, SaplSearchForm)
from sapl.base.models import Autor, TipoAutor, OperadorAutor
from sapl.comissoes.models import Comissao, Reuniao
from sapl.crud.base import CrudAux, make_pagination, Crud,\
    ListWithSearchForm, MasterDetailCrud
from sapl.materia.models import (Anexada, Autoria, DocumentoAcessorio, MateriaEmTramitacao, MateriaLegislativa,
                                 Proposicao, StatusTramitacao, TipoDocumento, TipoMateriaLegislativa, UnidadeTramitacao,
                                 MateriaAssunto)
from sapl.norma.models import NormaJuridica, TipoNormaJuridica
from sapl.parlamentares.models import (
    Filiacao, Legislatura, Mandato, Parlamentar, SessaoLegislativa)
from sapl.protocoloadm.models import (Anexado, DocumentoAdministrativo, Protocolo, StatusTramitacaoAdministrativo,
                                      TipoDocumentoAdministrativo)
from sapl.relatorios.views import (relatorio_materia_em_tramitacao, relatorio_materia_por_autor,
                                   relatorio_materia_por_ano_autor, relatorio_presenca_sessao,
                                   relatorio_historico_tramitacao, relatorio_fim_prazo_tramitacao, relatorio_atas,
                                   relatorio_audiencia, relatorio_normas_mes, relatorio_normas_vigencia,
                                   relatorio_historico_tramitacao_adm, relatorio_reuniao,
                                   relatorio_estatisticas_acesso_normas, relatorio_normas_por_autor,
                                   relatorio_documento_acessorio)
from sapl.sessao.models import (
    Bancada, PresencaOrdemDia, SessaoPlenaria, SessaoPlenariaPresenca, TipoSessaoPlenaria)
from sapl.settings import EMAIL_SEND_USER
from sapl.utils import (gerar_hash_arquivo, intervalos_tem_intersecao, mail_service_configured, parlamentares_ativos,
                        SEPARADOR_HASH_PROPOSICAO, show_results_filter_set, num_materias_por_tipo,
                        google_recaptcha_configured, sapl_as_sapn,
                        groups_remove_user, groups_add_user, get_client_ip)

from .forms import (AlterarSenhaForm, CasaLegislativaForm, ConfiguracoesAppForm, RelatorioAtasFilterSet,
                    RelatorioAudienciaFilterSet, RelatorioDataFimPrazoTramitacaoFilterSet,
                    RelatorioHistoricoTramitacaoFilterSet, RelatorioMateriasPorAnoAutorTipoFilterSet,
                    RelatorioMateriasPorAutorFilterSet, RelatorioMateriasTramitacaoFilterSet,
                    RelatorioPresencaSessaoFilterSet, RelatorioReuniaoFilterSet,
                    RelatorioNormasMesFilterSet, RelatorioNormasVigenciaFilterSet, EstatisticasAcessoNormasForm,
                    RelatorioHistoricoTramitacaoAdmFilterSet, RelatorioDocumentosAcessoriosFilterSet,
                    RelatorioNormasPorAutorFilterSet)
from .models import AppConfig, CasaLegislativa


def get_casalegislativa():
    return CasaLegislativa.objects.first()


class IndexView(TemplateView):
    def get(self, request, *args, **kwargs):
        if sapl_as_sapn():
            return redirect('/norma/pesquisar')
        return TemplateView.get(self, request, *args, **kwargs)


@method_decorator(ratelimit(key=lambda group, request: get_client_ip(request),
                            rate='20/m',
                            method=ratelimit.UNSAFE,
                            block=True), name='dispatch')
class LoginSapl(views.LoginView):
    template_name = 'base/login.html'
    authentication_form = LoginForm


class ConfirmarEmailView(TemplateView):
    template_name = "email/confirma.html"

    def get(self, request, *args, **kwargs):
        uid = urlsafe_base64_decode(self.kwargs['uidb64'])
        user = get_user_model().objects.get(id=uid)
        user.is_active = True
        user.save()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class RecuperarSenhaEmailView(PasswordResetView):
    logger = logging.getLogger(__name__)

    success_url = reverse_lazy('sapl.base:recuperar_senha_finalizado')
    email_template_name = 'base/recuperar_senha_email.html'
    html_email_template_name = 'base/recuperar_senha_email.html'
    template_name = 'base/recuperar_senha_email_form.html'
    from_email = EMAIL_SEND_USER
    form_class = RecuperarSenhaForm

    def get(self, request, *args, **kwargs):

        if not google_recaptcha_configured():
            self.logger.warning(_('Google Recaptcha não configurado!'))
            messages.error(request, _('Google Recaptcha não configurado!'))
            return redirect(request.META.get('HTTP_REFERER', '/'))

        return PasswordResetView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        if not google_recaptcha_configured():
            self.logger.warning(_('Google Recaptcha não configurado!'))
            messages.error(request, _('Google Recaptcha não configurado!'))
            return redirect(request.META.get('HTTP_REFERER', '/'))

        return PasswordResetView.post(self, request, *args, **kwargs)


class RecuperarSenhaFinalizadoView(PasswordResetDoneView):
    template_name = 'base/recupera_senha_email_enviado.html'


class RecuperarSenhaConfirmaView(PasswordResetConfirmView):
    success_url = reverse_lazy('sapl.base:recuperar_senha_completo')
    template_name = 'base/nova_senha_form.html'
    form_class = NovaSenhaForm


class RecuperarSenhaCompletoView(PasswordResetCompleteView):
    template_name = 'base/recuperar_senha_completo.html'


class TipoAutorCrud(CrudAux):
    model = TipoAutor
    help_topic = 'tipo-autor'

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ['descricao']
        form_class = TipoAutorForm

        @property
        def verbose_name(self):
            vn = super().verbose_name
            vn = "{} {}".format(vn, _('Externo ao SAPL'))
            return vn

    class ListView(CrudAux.ListView):
        template_name = "base/tipoautor_list.html"

        def get_queryset(self):
            qs = CrudAux.ListView.get_queryset(self)
            qs = qs.filter(content_type__isnull=True)
            return qs

        def get_context_data(self, **kwargs):
            context = CrudAux.ListView.get_context_data(self, **kwargs)

            context['tipos_sapl'] = TipoAutor.objects.filter(
                content_type__isnull=False)

            return context

    class TipoAutorMixin:

        def dispatch(self, request, *args, **kwargs):
            object = self.get_object()
            if object.content_type:
                raise PermissionDenied()
            return super().dispatch(request, *args, **kwargs)

    class UpdateView(TipoAutorMixin, CrudAux.UpdateView):
        pass

    class DetailView(TipoAutorMixin, CrudAux.DetailView):
        pass

    class DeleteView(TipoAutorMixin, CrudAux.DeleteView):
        pass


class AutorCrud(CrudAux):
    model = Autor
    help_topic = 'autor'

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ['nome', 'tipo', 'operadores']

        def send_mail_operadores(self):
            username = self.request.user.username

            if not mail_service_configured():
                self.logger.warning(_('Registro de Autor sem envio de email. '
                                      'Servidor de email não configurado.'))
                return

            try:
                self.logger.debug('user=' + username +
                                  '. Enviando email na criação de Autores.')

                kwargs = {}

                for user in self.object.operadores.all():

                    if not user.email:
                        self.logger.warning(
                            _('Registro de Autor sem envio de email. '
                              'Usuário sem um email cadastrado.'))
                        continue

                    kwargs['token'] = default_token_generator.make_token(user)
                    kwargs['uidb64'] = urlsafe_base64_encode(
                        force_bytes(user.pk))
                    assunto = "SAPL - Confirmação de Conta"
                    full_url = self.request.get_raw_uri()
                    url_base = full_url[:full_url.find('sistema') - 1]

                    mensagem = (
                        "Este e-mail foi utilizado para fazer cadastro no " +
                        "SAPL com o perfil de Autor. Agora você pode " +
                        "criar/editar/enviar Proposições.\n" +
                        "Seu nome de usuário é: " +
                        self.request.POST['username'] + "\n"
                        "Caso você não tenha feito este cadastro, por favor " +
                        "ignore esta mensagem. Caso tenha, clique " +
                        "no link abaixo\n" + url_base +
                        reverse('sapl.base:confirmar_email', kwargs=kwargs))
                    remetente = settings.EMAIL_SEND_USER
                    destinatario = [user.email]
                    send_mail(assunto, mensagem, remetente, destinatario,
                              fail_silently=False)
            except Exception as e:
                print(
                    _('Erro no envio de email na criação de Autores.'))
                self.logger.error(
                    'user=' + username + '. Erro no envio de email na criação de Autores. ' + str(e))

    class DeleteView(CrudAux.DeleteView):

        def delete(self, *args, **kwargs):
            self.object = self.get_object()

            grupo = Group.objects.filter(name='Autor')[0]
            lista_operadores = list(self.object.operadores.all())

            response = CrudAux.DeleteView.delete(self, *args, **kwargs)

            if not Autor.objects.filter(pk=kwargs['pk']).exists():
                for u in lista_operadores:
                    u.groups.remove(grupo)

            return response

    class DetailView(CrudAux.DetailView):

        def hook_operadores(self, obj):
            r = '<ul>{}</ul>'.format(
                ''.join(
                    [
                        '<li>{} - <i>({})</i> - '
                        '<small>{}</small>'
                        '</li>'.format(u.first_name, u, u.email)
                        for u in obj.operadores.all()
                    ]
                )

            )
            return 'Operadores', r

    class UpdateView(CrudAux.UpdateView):
        logger = logging.getLogger(__name__)
        layout_key = None
        form_class = AutorForm

        def get_success_url(self):
            self.send_mail_operadores()
            return super().get_success_url()

    class CreateView(CrudAux.CreateView):
        logger = logging.getLogger(__name__)
        form_class = AutorForm
        layout_key = None

        def get_success_url(self):
            self.send_mail_operadores()
            return super().get_success_url()

    class ListView(CrudAux.ListView):
        form_search_class = ListWithSearchForm

        def hook_operadores(self, *args, **kwargs):
            r = '<ul>{}</ul>'.format(
                ''.join(
                    [
                        '<li>{} - <i>({})</i></li>'.format(u.first_name, u)
                        for u in args[0].operadores.all()
                    ]
                )

            )
            return r, ''

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(nome__icontains=q_param)
                q |= Q(cargo__icontains=q_param)
                q |= Q(tipo__descricao__icontains=q_param)
                q |= Q(operadores__username__icontains=q_param)
                q |= Q(operadores__email__icontains=q_param)
                qs = qs.filter(q)
            return qs.distinct('nome', 'id').order_by('nome', 'id')


class RelatoriosListView(TemplateView):
    template_name = 'base/relatorios_list.html'

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)
        estatisticas_acesso_normas = AppConfig.objects.first().estatisticas_acesso_normas
        context['estatisticas_acesso_normas'] = True if estatisticas_acesso_normas == 'S' else False

        return context


class RelatorioMixin:
    def get(self, request, *args, **kwargs):
        super(RelatorioMixin, self).get(request)

        is_relatorio = request.GET.get('relatorio')
        context = self.get_context_data(filter=self.filterset)

        if is_relatorio:
            return self.relatorio(request, context)
        else:
            return self.render_to_response(context)


class RelatorioDocumentosAcessoriosView(RelatorioMixin, FilterView):
    model = DocumentoAcessorio
    filterset_class = RelatorioDocumentosAcessoriosFilterSet
    template_name = 'base/RelatorioDocumentosAcessorios_filter.html'
    relatorio = relatorio_documento_acessorio

    def get_context_data(self, **kwargs):
        context = super(
            RelatorioDocumentosAcessoriosView, self
        ).get_context_data(**kwargs)

        context['title'] = _('Documentos Acessórios das Matérias Legislativas')

        if not self.filterset.form.is_valid():
            return context

        query_dict = self.request.GET.copy()
        context['show_results'] = show_results_filter_set(query_dict)

        context['tipo_documento'] = str(
            TipoDocumento.objects.get(pk=self.request.GET['tipo'])
        )

        tipo_materia = self.request.GET['materia__tipo']
        if tipo_materia:
            context['tipo_materia'] = str(
                TipoMateriaLegislativa.objects.get(pk=tipo_materia)
            )
        else:
            context['tipo_materia'] = "Não selecionado"

        data_inicial = self.request.GET['data_0']
        data_final = self.request.GET['data_1']
        if not data_inicial:
            data_inicial = "Data Inicial não definida"
        if not data_final:
            data_final = "Data Final não definida"
        context['periodo'] = (
            data_inicial + ' - ' + data_final
        )

        return context


class RelatorioAtasView(RelatorioMixin, FilterView):
    model = SessaoPlenaria
    filterset_class = RelatorioAtasFilterSet
    template_name = 'base/RelatorioAtas_filter.html'
    relatorio = relatorio_atas

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Atas das Sessões Plenárias')

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)
        context['periodo'] = (
            self.request.GET['data_inicio_0'] +
            ' - ' + self.request.GET['data_inicio_1'])

        return context


class RelatorioPresencaSessaoView(RelatorioMixin, FilterView):
    logger = logging.getLogger(__name__)
    model = SessaoPlenaria
    filterset_class = RelatorioPresencaSessaoFilterSet
    template_name = 'base/RelatorioPresencaSessao_filter.html'
    relatorio = relatorio_presenca_sessao

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['title'] = _('Presença dos parlamentares nas sessões')

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        cd = self.filterset.form.cleaned_data
        if not cd['data_inicio'] and not cd['sessao_legislativa'] \
                and not cd['legislatura']:
            msg = _(
                "Formulário inválido! Preencha pelo menos algum dos campos Período, Legislatura ou Sessão Legislativa.")
            messages.error(self.request, msg)
            return context

        # Caso a data tenha sido preenchida, verifica se foi preenchida
        # corretamente
        if self.request.GET.get('data_inicio_0') and not self.request.GET.get('data_inicio_1'):
            msg = _("Formulário inválido! Preencha a data do Período Final.")
            messages.error(self.request, msg)
            return context

        if not self.request.GET.get('data_inicio_0') and self.request.GET.get('data_inicio_1'):
            msg = _("Formulário inválido! Preencha a data do Período Inicial.")
            messages.error(self.request, msg)
            return context

        param0 = {}

        legislatura_pk = self.request.GET.get('legislatura')
        if legislatura_pk:
            param0['sessao_plenaria__legislatura_id'] = legislatura_pk
            legislatura = Legislatura.objects.get(id=legislatura_pk)
            context['legislatura'] = legislatura

        sessao_legislativa_pk = self.request.GET.get('sessao_legislativa')
        if sessao_legislativa_pk:
            param0['sessao_plenaria__sessao_legislativa_id'] = sessao_legislativa_pk
            sessao_legislativa = SessaoLegislativa.objects.get(
                id=sessao_legislativa_pk)
            context['sessao_legislativa'] = sessao_legislativa

        tipo_sessao_plenaria_pk = self.request.GET.get('tipo')
        context['tipo'] = ''
        if tipo_sessao_plenaria_pk:
            param0['sessao_plenaria__tipo_id'] = tipo_sessao_plenaria_pk
            context['tipo'] = TipoSessaoPlenaria.objects.get(
                id=tipo_sessao_plenaria_pk)

        _range = []

        if ('data_inicio_0' in self.request.GET) and self.request.GET['data_inicio_0'] and \
                ('data_inicio_1' in self.request.GET) and self.request.GET['data_inicio_1']:
            where = context['object_list'].query.where
            _range = where.children[0].rhs

        elif legislatura_pk and not sessao_legislativa_pk:
            _range = [legislatura.data_inicio, legislatura.data_fim]

        elif sessao_legislativa_pk:
            _range = [sessao_legislativa.data_inicio,
                      sessao_legislativa.data_fim]

        param0.update({'sessao_plenaria__data_inicio__range': _range})

        # Parlamentares com Mandato no intervalo de tempo (Ativos)
        parlamentares_qs = parlamentares_ativos(
            _range[0], _range[1]).order_by('nome_parlamentar')
        parlamentares_id = parlamentares_qs.values_list('id', flat=True)

        # Presenças de cada Parlamentar em Sessões
        presenca_sessao = SessaoPlenariaPresenca.objects.filter(
            **param0).values_list('parlamentar_id').annotate(sessao_count=Count('id'))

        # Presenças de cada Ordem do Dia
        presenca_ordem = PresencaOrdemDia.objects.filter(
            **param0).values_list('parlamentar_id').annotate(sessao_count=Count('id'))

        total_ordemdia = PresencaOrdemDia.objects.filter(
            **param0).distinct('sessao_plenaria__id').order_by('sessao_plenaria__id').count()

        total_sessao = context['object_list'].count()

        username = self.request.user.username

        context['exibir_somente_titular'] = self.request.GET.get(
            'exibir_somente_titular') == 'on'
        context['exibir_somente_ativo'] = self.request.GET.get(
            'exibir_somente_ativo') == 'on'

        # Completa o dicionario as informacoes parlamentar/sessao/ordem
        parlamentares_presencas = []
        for p in parlamentares_qs:
            parlamentar = {}
            m = p.mandato_set.filter(Q(data_inicio_mandato__lte=_range[0], data_fim_mandato__gte=_range[1]) |
                                     Q(data_inicio_mandato__lte=_range[0], data_fim_mandato__isnull=True) |
                                     Q(data_inicio_mandato__gte=_range[0], data_fim_mandato__lte=_range[1]) |
                                     # mandato suplente
                                     Q(data_inicio_mandato__gte=_range[0], data_fim_mandato__lte=_range[1]))

            m = m.last()

            if not context['exibir_somente_titular'] and not context['exibir_somente_ativo']:
                parlamentar = {
                    'parlamentar': p,
                    'titular': m.titular if m else False,
                    'sessao_porc': 0,
                    'ordemdia_porc': 0
                }
            elif context['exibir_somente_titular'] and not context['exibir_somente_ativo']:
                if m and m.titular:
                    parlamentar = {
                        'parlamentar': p,
                        'titular': m.titular if m else False,
                        'sessao_porc': 0,
                        'ordemdia_porc': 0
                    }
                else:
                    continue
            elif not context['exibir_somente_titular'] and context['exibir_somente_ativo']:
                if p.ativo:
                    parlamentar = {
                        'parlamentar': p,
                        'titular': m.titular if m else False,
                        'sessao_porc': 0,
                        'ordemdia_porc': 0
                    }
                else:
                    continue
            elif context['exibir_somente_titular'] and context['exibir_somente_ativo']:
                if m and m.titular and p.ativo:
                    parlamentar = {
                        'parlamentar': p,
                        'titular': m.titular if m else False,
                        'sessao_porc': 0,
                        'ordemdia_porc': 0
                    }
                else:
                    continue
            else:
                continue

            try:
                self.logger.debug(
                    F'user={username}. Tentando obter presença do parlamentar (pk={p.id}).')
                sessao_count = presenca_sessao.get(parlamentar_id=p.id)[1]
            except ObjectDoesNotExist as e:
                self.logger.error(
                    F'user={username}. Erro ao obter presença do parlamentar (pk={p.id}). Definido como 0. {str(e)}')
                sessao_count = 0
            try:
                # Presenças de cada Ordem do Dia
                self.logger.info(
                    F'user={username}. Tentando obter PresencaOrdemDia para o parlamentar pk={p.id}.')
                ordemdia_count = presenca_ordem.get(parlamentar_id=p.id)[1]
            except ObjectDoesNotExist:
                self.logger.error(
                    F'user={username}. Erro ao obter PresencaOrdemDia para o parlamentar pk={p.id}. Definido como 0.')
                ordemdia_count = 0

            parlamentar.update({
                'sessao_count': sessao_count,
                'ordemdia_count': ordemdia_count
            })

            if total_sessao != 0:
                parlamentar.update({'sessao_porc': round(
                    sessao_count * 100 / total_sessao, 2)})
            if total_ordemdia != 0:
                parlamentar.update({'ordemdia_porc': round(
                    ordemdia_count * 100 / total_ordemdia, 2)})

            parlamentares_presencas.append(parlamentar)

        context['date_range'] = _range
        context['total_ordemdia'] = total_ordemdia
        context['total_sessao'] = context['object_list'].count()
        context['parlamentares'] = parlamentares_presencas
        context['periodo'] = f"{self.request.GET['data_inicio_0']} - {self.request.GET['data_inicio_1']}"
        context['sessao_legislativa'] = ''
        context['legislatura'] = ''
        context['exibir_ordem'] = self.request.GET.get(
            'exibir_ordem_dia') == 'on'

        if sessao_legislativa_pk:
            context['sessao_legislativa'] = SessaoLegislativa.objects.get(
                id=sessao_legislativa_pk)
        if legislatura_pk:
            context['legislatura'] = Legislatura.objects.get(id=legislatura_pk)
        # =====================================================================
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        return context


class RelatorioHistoricoTramitacaoView(RelatorioMixin, FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioHistoricoTramitacaoFilterSet
    template_name = 'base/RelatorioHistoricoTramitacao_filter.html'
    relatorio = relatorio_historico_tramitacao

    def get_context_data(self, **kwargs):
        context = super(RelatorioHistoricoTramitacaoView,
                        self).get_context_data(**kwargs)
        context['title'] = _(
            'Histórico de Tramitações de Matérias Legislativas')
        if not self.filterset.form.is_valid():
            return context
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)
        context['data_tramitacao'] = (self.request.GET['tramitacao__data_tramitacao_0'] + ' - ' +
                                      self.request.GET['tramitacao__data_tramitacao_1'])
        if self.request.GET['tipo']:
            tipo = self.request.GET['tipo']
            context['tipo'] = (
                str(TipoMateriaLegislativa.objects.get(id=tipo)))
        else:
            context['tipo'] = ''

        if self.request.GET['tramitacao__status']:
            tramitacao_status = self.request.GET['tramitacao__status']
            context['tramitacao__status'] = (
                str(StatusTramitacao.objects.get(id=tramitacao_status)))
        else:
            context['tramitacao__status'] = ''

        if self.request.GET['tramitacao__unidade_tramitacao_local']:
            context['tramitacao__unidade_tramitacao_local'] = \
                (str(UnidadeTramitacao.objects.get(
                    id=self.request.GET['tramitacao__unidade_tramitacao_local'])))
        else:
            context['tramitacao__unidade_tramitacao_local'] = ''

        if self.request.GET['tramitacao__unidade_tramitacao_destino']:
            context['tramitacao__unidade_tramitacao_destino'] = \
                (str(UnidadeTramitacao.objects.get(
                    id=self.request.GET['tramitacao__unidade_tramitacao_destino'])))
        else:
            context['tramitacao__unidade_tramitacao_destino'] = ''

        if self.request.GET['autoria__autor']:
            context['autoria__autor'] = \
                (str(Autor.objects.get(
                    id=self.request.GET['autoria__autor'])))
        else:
            context['autoria__autor'] = ''

        return context


class RelatorioDataFimPrazoTramitacaoView(RelatorioMixin, FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioDataFimPrazoTramitacaoFilterSet
    template_name = 'base/RelatorioDataFimPrazoTramitacao_filter.html'
    relatorio = relatorio_fim_prazo_tramitacao

    def get_context_data(self, **kwargs):
        context = super(RelatorioDataFimPrazoTramitacaoView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Relatório de Tramitações')
        if not self.filterset.form.is_valid():
            return context
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        context['data_tramitacao'] = (self.request.GET['tramitacao__data_fim_prazo_0'] + ' - ' +
                                      self.request.GET['tramitacao__data_fim_prazo_1'])

        if self.request.GET['ano']:
            ano_materia = self.request.GET['ano']
            for materia in MateriaLegislativa.objects.filter(ano=ano_materia):
                context['ano'] = (
                    materia.ano)
        else:
            context['ano'] = ''
        
        if self.request.GET['tipo']:
            tipo = self.request.GET['tipo']
            context['tipo'] = (
                str(TipoMateriaLegislativa.objects.get(id=tipo)))
        else:
            context['tipo'] = ''

        if self.request.GET['tramitacao__status']:
            tramitacao_status = self.request.GET['tramitacao__status']
            context['tramitacao__status'] = (
                str(StatusTramitacao.objects.get(id=tramitacao_status)))
        else:
            context['tramitacao__status'] = ''

        if self.request.GET['tramitacao__unidade_tramitacao_local']:
            context['tramitacao__unidade_tramitacao_local'] = \
                (str(UnidadeTramitacao.objects.get(
                    id=self.request.GET['tramitacao__unidade_tramitacao_local'])))
        else:
            context['tramitacao__unidade_tramitacao_local'] = ''

        if self.request.GET['tramitacao__unidade_tramitacao_destino']:
            context['tramitacao__unidade_tramitacao_destino'] = \
                (str(UnidadeTramitacao.objects.get(
                    id=self.request.GET['tramitacao__unidade_tramitacao_destino'])))
        else:
            context['tramitacao__unidade_tramitacao_destino'] = ''

        return context


class RelatorioReuniaoView(RelatorioMixin, FilterView):
    model = Reuniao
    filterset_class = RelatorioReuniaoFilterSet
    template_name = 'base/RelatorioReuniao_filter.html'
    relatorio = relatorio_reuniao

    def get_filterset_kwargs(self, filterset_class):
        super(RelatorioReuniaoView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(RelatorioReuniaoView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Reunião de Comissão')
        if not self.filterset.form.is_valid():
            return context
        qr = self.request.GET.copy()

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        if self.request.GET['comissao']:
            comissao = self.request.GET['comissao']
            context['comissao'] = (str(Comissao.objects.get(id=comissao)))
        else:
            context['comissao'] = ''

        return context


class RelatorioAudienciaView(RelatorioMixin, FilterView):
    model = AudienciaPublica
    filterset_class = RelatorioAudienciaFilterSet
    template_name = 'base/RelatorioAudiencia_filter.html'
    relatorio = relatorio_audiencia

    def get_filterset_kwargs(self, filterset_class):
        super(RelatorioAudienciaView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(RelatorioAudienciaView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Audiência Pública')
        if not self.filterset.form.is_valid():
            return context

        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        if self.request.GET['tipo']:
            tipo = self.request.GET['tipo']
            context['tipo'] = (str(TipoAudienciaPublica.objects.get(id=tipo)))
        else:
            context['tipo'] = ''

        return context


class RelatorioMateriasTramitacaoView(RelatorioMixin, FilterView):
    model = MateriaEmTramitacao
    filterset_class = RelatorioMateriasTramitacaoFilterSet
    template_name = 'base/RelatorioMateriasPorTramitacao_filter.html'
    relatorio = relatorio_materia_em_tramitacao

    paginate_by = 100

    total_resultados_tipos = {}

    def get_filterset_kwargs(self, filterset_class):
        data = super().get_filterset_kwargs(filterset_class)

        if data['data']:
            qs = data['queryset']

            ano_materia = data['data']['materia__ano']
            tipo_materia = data['data']['materia__tipo']
            unidade_tramitacao_destino = data['data']['tramitacao__unidade_tramitacao_destino']
            status_tramitacao = data['data']['tramitacao__status']
            autor = data['data']['materia__autores']

            kwargs = {}
            if ano_materia:
                kwargs['materia__ano'] = ano_materia
            if tipo_materia:
                kwargs['materia__tipo'] = tipo_materia
            if unidade_tramitacao_destino:
                kwargs['tramitacao__unidade_tramitacao_destino'] = unidade_tramitacao_destino
            if status_tramitacao:
                kwargs['tramitacao__status'] = status_tramitacao
            if autor:
                kwargs['materia__autores'] = autor

            qs = qs.filter(**kwargs)
            data['queryset'] = qs

            self.total_resultados_tipos = num_materias_por_tipo(
                qs, "materia__tipo")

        return data

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('materia__tipo').filter(
            materia__em_tramitacao=True
        ).exclude(
            tramitacao__status__indicador='F'
        ).order_by('-materia__ano', '-materia__numero')
        return qs

    def get_context_data(self, **kwargs):
        context = super(
            RelatorioMateriasTramitacaoView, self
        ).get_context_data(**kwargs)

        context['title'] = _('Matérias em Tramitação')

        if not self.filterset.form.is_valid():
            return context

        qr = self.request.GET.copy()

        context['qtdes'] = self.total_resultados_tipos
        context['ano'] = (self.request.GET['materia__ano'])

        if self.request.GET['materia__tipo']:
            tipo = self.request.GET['materia__tipo']
            context['tipo'] = (
                str(TipoMateriaLegislativa.objects.get(id=tipo))
            )
        else:
            context['tipo'] = ''

        if self.request.GET['tramitacao__status']:
            tramitacao_status = self.request.GET['tramitacao__status']
            context['tramitacao__status'] = (
                str(StatusTramitacao.objects.get(id=tramitacao_status))
            )
        else:
            context['tramitacao__status'] = ''

        if self.request.GET['tramitacao__unidade_tramitacao_destino']:
            context['tramitacao__unidade_tramitacao_destino'] = (
                str(UnidadeTramitacao.objects.get(
                    id=self.request.GET['tramitacao__unidade_tramitacao_destino']
                ))
            )
        else:
            context['tramitacao__unidade_tramitacao_destino'] = ''

        if self.request.GET['materia__autores']:
            autor = self.request.GET['materia__autores']
            context['materia__autor'] = (
                str(Autor.objects.get(id=autor))
            )
        else:
            context['materia__autor'] = ''
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''
        context['show_results'] = show_results_filter_set(qr)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages
        )
        context['NO_ENTRIES_MSG'] = 'Nenhum encontrado.'

        return context


class RelatorioMateriasPorAnoAutorTipoView(RelatorioMixin, FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioMateriasPorAnoAutorTipoFilterSet
    template_name = 'base/RelatorioMateriasPorAnoAutorTipo_filter.html'
    relatorio = relatorio_materia_por_ano_autor

    def get_materias_autor_ano(self, ano, primeiro_autor):

        autorias = Autoria.objects.filter(materia__ano=ano, primeiro_autor=primeiro_autor).values(
            'autor',
            'materia__tipo__sigla',
            'materia__tipo__descricao').annotate(
                total=Count('materia__tipo')).order_by(
                    'autor',
                    'materia__tipo')

        autores_ids = set([i['autor'] for i in autorias])

        autores = dict((a.id, a) for a in Autor.objects.filter(
            id__in=autores_ids))

        relatorio = []
        visitados = set()
        curr = None

        for a in autorias:
            # se mudou autor, salva atual, caso existente, e reinicia `curr`
            if a['autor'] not in visitados:
                if curr:
                    relatorio.append(curr)

                curr = {}
                curr['autor'] = autores[a['autor']]
                curr['materia'] = []
                curr['total'] = 0

                visitados.add(a['autor'])

            # atualiza valores
            curr['materia'].append((a['materia__tipo__descricao'], a['total']))
            curr['total'] += a['total']
        # adiciona o ultimo
        relatorio.append(curr)

        return relatorio

    def get_filterset_kwargs(self, filterset_class):
        super(RelatorioMateriasPorAnoAutorTipoView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(RelatorioMateriasPorAnoAutorTipoView,
                        self).get_context_data(**kwargs)

        context['title'] = _('Matérias por Ano, Autor e Tipo')
        if not self.filterset.form.is_valid():
            return context
        qs = context['object_list']
        context['qtdes'] = num_materias_por_tipo(qs)

        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)
        context['ano'] = self.request.GET['ano']

        if 'ano' in self.request.GET and self.request.GET['ano']:
            ano = int(self.request.GET['ano'])
            context['relatorio'] = self.get_materias_autor_ano(ano, True)
            context['corelatorio'] = self.get_materias_autor_ano(ano, False)
        else:
            context['relatorio'] = []

        return context


class RelatorioMateriasPorAutorView(RelatorioMixin, FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioMateriasPorAutorFilterSet
    template_name = 'base/RelatorioMateriasPorAutor_filter.html'
    relatorio = relatorio_materia_por_autor

    def get_filterset_kwargs(self, filterset_class):
        super().get_filterset_kwargs(filterset_class)
        kwargs = {'data': self.request.GET or None}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Matérias por Autor')
        if not self.filterset.form.is_valid():
            return context

        qs = context['object_list']
        context['materias_resultado'] = list(OrderedDict.fromkeys(qs))
        context['qtdes'] = num_materias_por_tipo(qs)

        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)
        if self.request.GET['tipo']:
            tipo = int(self.request.GET['tipo'])
            context['tipo'] = (
                str(TipoMateriaLegislativa.objects.get(id=tipo)))
        else:
            context['tipo'] = ''
        if self.request.GET['autoria__autor']:
            autor = int(self.request.GET['autoria__autor'])
            context['autor'] = (str(Autor.objects.get(id=autor)))
        else:
            context['autor'] = ''
        context['periodo'] = (
            self.request.GET['data_apresentacao_0'] +
            ' - ' + self.request.GET['data_apresentacao_1'])

        return context


class RelatorioMateriaAnoAssuntoView(ListView):
    template_name = 'base/RelatorioMateriasAnoAssunto.html'

    def get_queryset(self):
        return MateriaAssunto.objects.all().values(
            'assunto_id',
            assunto_materia=F('assunto__assunto'),
            ano=F('materia__ano')).annotate(
            total=Count('assunto_id')).order_by('-materia__ano', 'assunto_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Matérias por Ano e Assunto')

        # In[10]: MateriaAssunto.objects.all().values(
        #     ...:             'materia__ano').annotate(
        #     ...: total = Count('materia__ano')).order_by('-materia__ano')

        mat = MateriaLegislativa.objects.filter(
            materiaassunto__isnull=True).values(
            'ano').annotate(
            total=Count('ano')).order_by('-ano')

        context.update({"materias_sem_assunto": mat})
        return context


class RelatorioNormasPublicadasMesView(RelatorioMixin, FilterView):
    model = NormaJuridica
    filterset_class = RelatorioNormasMesFilterSet
    template_name = 'base/RelatorioNormaMes_filter.html'
    relatorio = relatorio_normas_mes

    def get_context_data(self, **kwargs):
        context = super(RelatorioNormasPublicadasMesView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Normas')

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)
        context['ano'] = self.request.GET['ano']

        normas_mes = collections.OrderedDict()
        meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
                 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        for norma in context['object_list']:
            if not meses[norma.data.month] in normas_mes:
                normas_mes[meses[norma.data.month]] = []
            normas_mes[meses[norma.data.month]].append(norma)

        context['normas_mes'] = normas_mes

        quant_normas_mes = {}
        for key in normas_mes.keys():
            quant_normas_mes[key] = len(normas_mes[key])

        context['quant_normas_mes'] = quant_normas_mes

        return context


class RelatorioNormasVigenciaView(RelatorioMixin, FilterView):
    model = NormaJuridica
    filterset_class = RelatorioNormasVigenciaFilterSet
    template_name = 'base/RelatorioNormasVigencia_filter.html'
    relatorio = relatorio_normas_vigencia

    def get_filterset_kwargs(self, filterset_class):
        super(RelatorioNormasVigenciaView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}
        qs = self.get_queryset().order_by('data').distinct()
        if kwargs['data']:
            ano = kwargs['data']['ano']
            vigencia = kwargs['data']['vigencia']
            if ano:
                qs = qs.filter(ano=ano)

            if vigencia == 'True':
                qs_dt_not_null = qs.filter(data_vigencia__isnull=True)
                qs = (qs_dt_not_null | qs.filter(
                    data_vigencia__gte=datetime.datetime.now().date())).distinct()
            else:
                qs = qs.filter(
                    data_vigencia__lt=datetime.datetime.now().date())

        kwargs.update({
            'queryset': qs
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(RelatorioNormasVigenciaView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Normas por vigência')

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        normas_totais = NormaJuridica.objects.filter(
            ano=self.request.GET['ano'])

        context['quant_total'] = len(normas_totais)
        if self.request.GET['vigencia'] == 'True':
            context['vigencia'] = 'Vigente'
            context['quant_vigente'] = len(context['object_list'])
            context['quant_nao_vigente'] = context['quant_total'] - \
                context['quant_vigente']
        else:
            context['vigencia'] = 'Não vigente'
            context['quant_nao_vigente'] = len(context['object_list'])
            context['quant_vigente'] = context['quant_total'] - \
                context['quant_nao_vigente']

        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)
        context['ano'] = self.request.GET['ano']

        return context


class EstatisticasAcessoNormas(TemplateView):
    template_name = 'base/EstatisticasAcessoNormas_filter.html'

    def get(self, request, *args, **kwargs):
        context = super(EstatisticasAcessoNormas,
                        self).get_context_data(**kwargs)
        context['title'] = _('Normas')

        form = EstatisticasAcessoNormasForm(request.GET or None)
        context['form'] = form

        if not form.is_valid():
            return self.render_to_response(context)

        context['ano'] = self.request.GET['ano']

        query = '''
                select norma_id, ano, extract(month from horario_acesso) as mes, count(*)
                from norma_normaestatisticas
                where ano = {}
                group by mes, ano, norma_id
                order by mes desc;
                '''.format(context['ano'])
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        normas_mes = collections.OrderedDict()
        meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
                 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}

        for row in rows:
            if not meses[int(row[2])] in normas_mes:
                normas_mes[meses[int(row[2])]] = []
            norma_est = [NormaJuridica.objects.get(id=row[0]), row[3]]
            normas_mes[meses[int(row[2])]].append(norma_est)

        # Ordena por acesso e limita em 5
        for n in normas_mes:
            sorted_by_value = sorted(
                normas_mes[n], key=lambda kv: kv[1], reverse=True)
            normas_mes[n] = sorted_by_value[0:5]

        context['normas_mes'] = normas_mes

        is_relatorio = request.GET.get('relatorio')

        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        if is_relatorio:
            return relatorio_estatisticas_acesso_normas(self, request, context)
        else:
            return self.render_to_response(context)


class ListarInconsistenciasView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/lista_inconsistencias.html'
    context_object_name = 'tabela_inconsistencias'
    permission_required = ('base.list_appconfig',)

    def get_queryset(self):
        tabela = []
        tabela.append(
            ('protocolos_duplicados',
             'Protocolos duplicados',
             len(protocolos_duplicados())
             )
        )
        tabela.append(
            ('protocolos_com_materias',
             'Protocolos que excedem o limite de matérias vinculadas',
             len(protocolos_com_materias())
             )
        )
        tabela.append(
            ('materias_protocolo_inexistente',
             'Matérias Legislativas com protocolo inexistente',
             len(materias_protocolo_inexistente())
             )
        )
        tabela.append(
            ('filiacoes_sem_data_filiacao',
             'Filiações sem data filiação',
             len(filiacoes_sem_data_filiacao())
             )
        )
        tabela.append(
            ('mandato_sem_data_inicio',
             'Mandatos sem data inicial',
             len(mandato_sem_data_inicio())
             )
        )
        tabela.append(
            ('parlamentares_duplicados',
             'Parlamentares duplicados',
             len(parlamentares_duplicados())
             )
        )
        tabela.append(
            ('parlamentares_mandatos_intersecao',
             'Parlamentares com mandatos em interseção',
             len(parlamentares_mandatos_intersecao())
             )
        )
        tabela.append(
            ('parlamentares_filiacoes_intersecao',
             'Parlamentares com filiações em interseção',
             len(parlamentares_filiacoes_intersecao())
             )
        )
        tabela.append(
            ('autores_duplicados',
             'Autores duplicados',
             len(autores_duplicados())
             )
        )
        tabela.append(
            ('bancada_comissao_autor_externo',
             'Bancadas e Comissões com autor externo',
             len(bancada_comissao_autor_externo())
             )
        )
        tabela.append(
            ('legislatura_infindavel',
             'Legislaturas sem data fim',
             len(legislatura_infindavel())
             )
        )
        tabela.append(
            ('anexadas_ciclicas',
             'Matérias Anexadas cíclicas',
             len(materias_anexadas_ciclicas())
             )
        )
        tabela.append(
            ('anexados_ciclicos',
             'Documentos Anexados cíclicos',
             len(anexados_ciclicos(False))
             )
        )
        return tabela


def materias_anexadas_ciclicas():
    ciclos = []

    for a in Anexada.objects.select_related('materia_principal',
                                            'materia_anexada',
                                            'materia_principal__tipo',
                                            'materia_anexada__tipo'):
        visitados = [a.materia_principal]
        anexadas = [a.materia_anexada]
        while len(anexadas) > 0:
            ma = anexadas.pop()
            if ma not in visitados:
                visitados.append(ma)
                anexadas.extend(
                    [a.materia_anexada for a in Anexada.objects.filter(materia_principal=ma)])
            else:
                ciclo_list = visitados + [ma]
                ciclos.append(ciclo_list)

    """
    Remove ciclos repetidos (ou semanticamente equivalentes).
    Exemplo: A -> B -> A e B -> A -> B
    """
    ciclos_set = []
    ciclos_unique = [e for e in ciclos if is_ciclo_unique(e, ciclos_set)]

    return ciclos_unique


def is_ciclo_unique(ciclo, ciclos_set):
    if set(ciclo) not in ciclos_set:
        ciclos_set.append(set(ciclo))
        return True
    else:
        return False


def anexados_ciclicos(ofMateriaLegislativa):
    ciclicos = []

    if ofMateriaLegislativa:
        principais = Anexada.objects.values(
            'materia_principal'
        ).annotate(
            count=Count('materia_principal')
        ).filter(count__gt=0).order_by('-data_anexacao')
    else:
        principais = Anexado.objects.values(
            'documento_principal'
        ).annotate(
            count=Count('documento_principal')
        ).filter(count__gt=0).order_by('-data_anexacao')

    for principal in principais:
        anexados_total = []

        if ofMateriaLegislativa:
            anexados = Anexada.objects.filter(
                materia_principal=principal['materia_principal']
            ).order_by('-data_anexacao')
        else:
            anexados = Anexado.objects.filter(
                documento_principal=principal['documento_principal']
            ).order_by('-data_anexacao')

        anexados_temp = list(anexados)
        while anexados_temp:
            anexado = anexados_temp.pop()
            if ofMateriaLegislativa:
                if anexado.materia_anexada not in anexados_total:
                    if not principal['materia_principal'] == anexado.materia_anexada.pk:
                        anexados_total.append(anexado.materia_anexada)
                        anexados_anexado = Anexada.objects.filter(
                            materia_principal=anexado.materia_anexada
                        )
                        anexados_temp.extend(anexados_anexado)
                    else:
                        ciclicos.append(
                            (anexado.data_anexacao, anexado.materia_principal, anexado.materia_anexada))
            else:
                if anexado.documento_anexado not in anexados_total:
                    if not principal['documento_principal'] == anexado.documento_anexado.pk:
                        anexados_total.append(anexado.documento_anexado)
                        anexados_anexado = Anexado.objects.filter(
                            documento_principal=anexado.documento_anexado
                        )
                        anexados_temp.extend(anexados_anexado)
                    else:
                        ciclicos.append(
                            (anexado.data_anexacao, anexado.documento_principal, anexado.documento_anexado))

    return ciclicos


class ListarAnexadosCiclicosView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/anexados_ciclicos.html'
    context_object_name = 'anexados_ciclicos'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return anexados_ciclicos(False)

    def get_context_data(self, **kwargs):
        context = super(
            ListarAnexadosCiclicosView, self
        ).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages
        )
        context['NO_ENTRIES_MSG'] = 'Nenhum encontrado.'

        return context


class ListarAnexadasCiclicasView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/anexadas_ciclicas.html'
    context_object_name = 'anexadas_ciclicas'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return materias_anexadas_ciclicas()

    def get_context_data(self, **kwargs):
        context = super(
            ListarAnexadasCiclicasView, self
        ).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages
        )
        context['NO_ENTRIES_MSG'] = 'Nenhuma encontrada.'

        return context


def legislatura_infindavel():
    return Legislatura.objects.filter(data_fim__isnull=True).order_by('-numero')


class ListarLegislaturaInfindavelView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/legislatura_infindavel.html'
    context_object_name = 'legislatura_infindavel'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return legislatura_infindavel()

    def get_context_data(self, **kwargs):
        context = super(
            ListarLegislaturaInfindavelView, self
        ).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhuma encontrada.'
        return context


def bancada_comissao_autor_externo():
    tipo_autor_externo = TipoAutor.objects.filter(descricao='Externo')

    lista_bancada_autor_externo = []
    for bancada in Bancada.objects.all().order_by('nome'):
        autor_externo = bancada.autor.filter(tipo__in=tipo_autor_externo)

        if autor_externo:
            q_autor_externo = bancada.autor.get(tipo__in=tipo_autor_externo)
            lista_bancada_autor_externo.append(
                (q_autor_externo, bancada, 'Bancada', 'sistema/bancada')
            )

    lista_comissao_autor_externo = []
    for comissao in Comissao.objects.all().order_by('nome'):
        autor_externo = comissao.autor.filter(tipo__in=tipo_autor_externo)

        if autor_externo:
            q_autor_externo = comissao.autor.get(tipo__in=tipo_autor_externo)
            lista_comissao_autor_externo.append(
                (q_autor_externo, comissao, 'Comissão', 'comissao')
            )

    return lista_bancada_autor_externo + lista_comissao_autor_externo


class ListarBancadaComissaoAutorExternoView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/bancada_comissao_autor_externo.html'
    context_object_name = 'bancada_comissao_autor_externo'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return bancada_comissao_autor_externo()

    def get_context_data(self, **kwargs):
        context = super(
            ListarBancadaComissaoAutorExternoView, self
        ).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhuma encontrada.'
        return context


def autores_duplicados():
    return [autor for autor in Autor.objects.values('nome').annotate(count=Count('nome')).filter(count__gt=1)]


class ListarAutoresDuplicadosView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/autores_duplicados.html'
    context_object_name = 'autores_duplicados'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return autores_duplicados()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhum encontrado.'
        return context


def parlamentares_filiacoes_intersecao():
    intersecoes = []

    for parlamentar in Parlamentar.objects.all().order_by('nome_parlamentar'):
        filiacoes = parlamentar.filiacao_set.all()
        combinacoes = itertools.combinations(filiacoes, 2)

        for c in combinacoes:
            data_filiacao1 = c[0].data
            data_desfiliacao1 = c[0].data_desfiliacao if c[0].data_desfiliacao else timezone.now(
            ).date()

            data_filiacao2 = c[1].data
            data_desfiliacao2 = c[1].data_desfiliacao if c[1].data_desfiliacao else timezone.now(
            ).date()

            if data_filiacao1 and data_filiacao2:
                exists = intervalos_tem_intersecao(
                    data_filiacao1, data_desfiliacao1,
                    data_filiacao2, data_desfiliacao2)
                if exists:
                    intersecoes.append((parlamentar, c[0], c[1]))
    return intersecoes


class ListarParlFiliacoesIntersecaoView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/parlamentares_filiacoes_intersecao.html'
    context_object_name = 'parlamentares_filiacoes_intersecao'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return parlamentares_filiacoes_intersecao()

    def get_context_data(self, **kwargs):
        context = super(
            ListarParlFiliacoesIntersecaoView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhum encontrado.'
        return context


def parlamentares_mandatos_intersecao():
    intersecoes = []

    for parlamentar in Parlamentar.objects.all().order_by('nome_parlamentar'):
        mandatos = parlamentar.mandato_set.all()
        combinacoes = itertools.combinations(mandatos, 2)

        for c in combinacoes:
            data_inicio_mandato1 = c[0].data_inicio_mandato
            data_fim_mandato1 = c[0].data_fim_mandato if c[0].data_fim_mandato else timezone.now(
            ).date()

            data_inicio_mandato2 = c[1].data_inicio_mandato
            data_fim_mandato2 = c[1].data_fim_mandato if c[1].data_fim_mandato else timezone.now(
            ).date()

            if data_inicio_mandato1 and data_inicio_mandato2:
                exists = intervalos_tem_intersecao(
                    data_inicio_mandato1, data_fim_mandato1,
                    data_inicio_mandato2, data_fim_mandato2)
                if exists:
                    intersecoes.append((parlamentar, c[0], c[1]))

    return intersecoes


class ListarParlMandatosIntersecaoView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/parlamentares_mandatos_intersecao.html'
    context_object_name = 'parlamentares_mandatos_intersecao'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return parlamentares_mandatos_intersecao()

    def get_context_data(self, **kwargs):
        context = super(
            ListarParlMandatosIntersecaoView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhum encontrado.'
        return context


def parlamentares_duplicados():
    return [parlamentar for parlamentar in Parlamentar.objects.values(
        'nome_parlamentar').order_by('nome_parlamentar').annotate(count=Count(
            'nome_parlamentar')).filter(count__gt=1)]


class ListarParlamentaresDuplicadosView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/parlamentares_duplicados.html'
    context_object_name = 'parlamentares_duplicados'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return parlamentares_duplicados()

    def get_context_data(self, **kwargs):
        context = super(
            ListarParlamentaresDuplicadosView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhum encontrado.'
        return context


def mandato_sem_data_inicio():
    return Mandato.objects.filter(data_inicio_mandato__isnull=True).order_by('parlamentar')


def get_estatistica(request):
    materias = MateriaLegislativa.objects.all()
    normas = NormaJuridica.objects.all()

    datas = [
        materias.order_by(
            '-data_ultima_atualizacao').values_list('data_ultima_atualizacao', flat=True)
        .exclude(data_ultima_atualizacao__isnull=True).first(),
        normas.order_by(
            '-data_ultima_atualizacao').values_list('data_ultima_atualizacao', flat=True)
        .exclude(data_ultima_atualizacao__isnull=True).first()
    ]

    max_data = max(datas) if datas[0] and datas[1] else next(
        iter([i for i in datas if i is not None]), '')

    return JsonResponse({
        "data_ultima_atualizacao": max_data,
        "num_materias_legislativas": materias.count(),
        "num_normas_juridicas ": normas.count(),
        "num_parlamentares": Parlamentar.objects.all().count(),
        "num_sessoes_plenarias": SessaoPlenaria.objects.all().count()
    })


class ListarMandatoSemDataInicioView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/mandato_sem_data_inicio.html'
    context_object_name = 'mandato_sem_data_inicio'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return mandato_sem_data_inicio()

    def get_context_data(self, **kwargs):
        context = super(
            ListarMandatoSemDataInicioView, self
        ).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhum encontrado.'
        return context


def filiacoes_sem_data_filiacao():
    return Filiacao.objects.filter(data__isnull=True).order_by('parlamentar')


class ListarFiliacoesSemDataFiliacaoView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/filiacoes_sem_data_filiacao.html'
    context_object_name = 'filiacoes_sem_data_filiacao'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return filiacoes_sem_data_filiacao()

    def get_context_data(self, **kwargs):
        context = super(
            ListarFiliacoesSemDataFiliacaoView, self
        ).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhuma encontrada.'
        return context


def materias_protocolo_inexistente():
    materias = []
    for materia in MateriaLegislativa.objects.filter(numero_protocolo__isnull=False).order_by('-ano', 'numero'):
        exists = Protocolo.objects.filter(
            ano=materia.ano, numero=materia.numero_protocolo).exists()
        if not exists:
            materias.append(
                (materia, materia.ano, materia.numero_protocolo))
    return materias


class ListarMatProtocoloInexistenteView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/materias_protocolo_inexistente.html'
    context_object_name = 'materias_protocolo_inexistente'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return materias_protocolo_inexistente()

    def get_context_data(self, **kwargs):
        context = super(
            ListarMatProtocoloInexistenteView, self
        ).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhuma encontrada.'
        return context


def protocolos_com_materias():
    protocolos = {}

    for m in MateriaLegislativa.objects.filter(numero_protocolo__isnull=False).order_by('-ano', 'numero_protocolo'):
        if Protocolo.objects.filter(numero=m.numero_protocolo, ano=m.ano).exists():
            key = "{}/{}".format(m.numero_protocolo, m.ano)
            val = protocolos.get(key, list())
            val.append(m)
            protocolos[key] = val

    return [(v[0], len(v)) for (k, v) in protocolos.items() if len(v) > 1]


class ListarProtocolosComMateriasView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/protocolos_com_materias.html'
    context_object_name = 'protocolos_com_materias'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return protocolos_com_materias()

    def get_context_data(self, **kwargs):
        context = super(
            ListarProtocolosComMateriasView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhum encontrado.'
        return context


def protocolos_duplicados():
    return [
        protocolo for protocolo in Protocolo.objects.values(
            'numero', 'ano').order_by('-ano', 'numero').annotate(total=Count('numero')).filter(total__gt=1)
    ]


class ListarProtocolosDuplicadosView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'base/protocolos_duplicados.html'
    context_object_name = 'protocolos_duplicados'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        return protocolos_duplicados()

    def get_context_data(self, **kwargs):
        context = super(
            ListarProtocolosDuplicadosView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context[
            'NO_ENTRIES_MSG'
        ] = 'Nenhum encontrado.'
        return context


class UserCrud(Crud):
    model = get_user_model()

    class BaseMixin(Crud.BaseMixin):
        list_field_names = [
            'usuario', 'groups', 'is_active'
        ]

        def resolve_url(self, suffix, args=None):
            return reverse('sapl.base:%s' % self.url_name(suffix),
                           args=args)

        def get_layout(self):
            return super().get_layout(
                'base/layouts.yaml'
            )

        def get_context_object_name(self, *args, **kwargs):
            return None

    class CreateView(Crud.CreateView):
        form_class = UserAdminForm
        layout_key = None

    class UpdateView(Crud.UpdateView):
        form_class = UserAdminForm
        layout_key = None

        def get_form_kwargs(self):
            kwargs = Crud.UpdateView.get_form_kwargs(self)
            kwargs['user_session'] = self.request.user
            granular = self.request.GET.get('granular', None)
            if not granular is None:
                kwargs['granular'] = granular
            return kwargs

    class DetailView(Crud.DetailView):
        layout_key = 'UserDetail'

        def hook_usuario(self, obj):
            return 'Usuário', '{}<br><small>{}</small>'.format(
                obj.get_full_name() or '...',
                obj.email
            )

        def hook_auth_token(self, obj):
            return 'Token', str(obj.auth_token)

        def hook_username(self, obj):
            return 'username', obj.username

        def get_context_data(self, **kwargs):
            context = Crud.DetailView.get_context_data(self, **kwargs)
            context['title'] = '{} <i>({})</i><br><small>{}</small>'.format(
                self.object.get_full_name() or '...',
                self.object.username,
                self.object.email
            )
            return context

        @property
        def extras_url(self):
            btns = [
                (
                    '{}?granular'.format(reverse('sapl.base:user_update',
                                                 kwargs={'pk': self.object.pk})),
                    'btn-outline-primary',
                    _('Edição granular')
                )
            ]

            return btns

    class ListView(Crud.ListView):
        form_search_class = ListWithSearchForm
        paginate_by = 256

        def get_context_data(self, **kwargs):
            context = Crud.ListView.get_context_data(self, **kwargs)
            context['subnav_template_name'] = None
            context['title'] = _('Usuários')
            return context

        def hook_header_usuario(self, *args, **kwargs):
            return 'Usuário'

        def hook_header_groups(self, *args, **kwargs):
            return 'Grupos'

        def hook_header_is_active(self, *args, **kwargs):
            return 'Ativo'

        def hook_usuario(self, *args, **kwargs):
            return '{} <i>({})</i><br><small>{}</small>'.format(
                args[0].get_full_name() or '...',
                args[0].username,
                args[0].email
            ), args[2]

        def get_queryset(self):
            qs = self.model.objects.all()
            q_param = self.request.GET.get('q', '')
            if q_param:
                q = Q(first_name__icontains=q_param)
                q |= Q(last_name__icontains=q_param)
                q |= Q(email__icontains=q_param)
                q |= Q(username__icontains=q_param)
                q |= Q(groups__name__icontains=q_param)
                qs = qs.filter(q)

            return qs.distinct('id').order_by('-id')


class CasaLegislativaCrud(CrudAux):
    model = CasaLegislativa

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ['codigo', 'nome', 'sigla']
        form_class = CasaLegislativaForm

    class ListView(CrudAux.ListView):

        def get(self, request, *args, **kwargs):
            casa = get_casalegislativa()
            if casa:
                return HttpResponseRedirect(
                    reverse('sapl.base:casalegislativa_detail',
                            kwargs={'pk': casa.pk}))
            else:
                return HttpResponseRedirect(
                    reverse('sapl.base:casalegislativa_create'))

    class DetailView(CrudAux.DetailView):

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(
                reverse('sapl.base:casalegislativa_update',
                        kwargs={'pk': self.kwargs['pk']}))


class HelpTopicView(TemplateView):
    logger = logging.getLogger(__name__)

    def get_template_names(self):

        username = self.request.user.username
        topico = self.kwargs['topic']
        try:
            self.logger.debug('user=' + username +
                              '. Tentando obter template %s.html.' % topico)
            get_template('ajuda/%s.html' % topico)
        except TemplateDoesNotExist as e:
            self.logger.error(
                'user=' + username + '. Erro ao obter template {}.html. Template não existe. '.format(topico) + str(e))
            raise Http404()
        return ['ajuda/%s.html' % topico]


class AppConfigCrud(CrudAux):
    model = AppConfig

    class BaseMixin(CrudAux.BaseMixin):
        form_class = ConfiguracoesAppForm
        list_url = ''
        create_url = ''

        def form_valid(self, form):
            recibo_prop_atual = AppConfig.objects.last().receber_recibo_proposicao
            recibo_prop_novo = self.request.POST['receber_recibo_proposicao']
            if recibo_prop_novo == 'False' and recibo_prop_atual:
                props = Proposicao.objects.filter(
                    hash_code='', data_recebimento__isnull=True).exclude(data_envio__isnull=True)
                for prop in props:
                    try:
                        self.gerar_hash(prop)
                    except ValidationError as e:
                        form.add_error('receber_recibo_proposicao', e)
                        msg = _(
                            "Não foi possível mudar a configuração porque a Proposição {} não possui texto original vinculado!".format(prop))
                        messages.error(self.request, msg)
                        return super().form_invalid(form)
            return super().form_valid(form)

        def gerar_hash(self, inst):
            if inst.texto_original:
                try:
                    inst.hash_code = gerar_hash_arquivo(
                        inst.texto_original.path, str(inst.pk))
                    inst.save()
                except IOError:
                    raise ValidationError(
                        "Existem proposicoes com arquivos inexistentes.")
            elif inst.texto_articulado.exists():
                ta = inst.texto_articulado.first()
                inst.hash_code = 'P' + ta.hash() + SEPARADOR_HASH_PROPOSICAO + str(inst.pk)
                inst.save()

    class CreateView(CrudAux.CreateView):

        def get(self, request, *args, **kwargs):
            app_config = AppConfig.objects.first()

            if not app_config:
                app_config = AppConfig()
                app_config.save()

            return HttpResponseRedirect(
                reverse('sapl.base:appconfig_update',
                        kwargs={'pk': app_config.pk}))

    class UpdateView(CrudAux.UpdateView):

        template_name = 'base/AppConfig.html'
        form_class = ConfiguracoesAppForm

        def form_valid(self, form):
            numeracao = AppConfig.objects.last().sequencia_numeracao_protocolo
            numeracao_antiga = AppConfig.objects.last().inicio_numeracao_protocolo

            self.object = form.save()
            numeracao_nova = self.object.inicio_numeracao_protocolo

            if numeracao_nova != numeracao_antiga:
                if numeracao == 'A':
                    numero_max = Protocolo.objects.filter(
                        ano=timezone.now().year
                    ).aggregate(Max('numero'))['numero__max']
                elif numeracao == 'L':
                    legislatura = Legislatura.objects.filter(
                        data_inicio__year__lte=timezone.now().year,
                        data_fim__year__gte=timezone.now().year
                    ).first()

                    data_inicio = legislatura.data_inicio
                    data_fim = legislatura.data_fim

                    data_inicio_utc = from_date_to_datetime_utc(data_inicio)
                    data_fim_utc = from_date_to_datetime_utc(data_fim)

                    numero_max = Protocolo.objects.filter(
                        Q(data__isnull=False, data__gte=data_inicio, data__lte=data_fim) |
                        Q(
                            timestamp__isnull=False, timestamp__gte=data_inicio_utc,
                            timestamp__lte=data_fim_utc
                        ) | Q(
                            timestamp_data_hora_manual__isnull=False,
                            timestamp_data_hora_manual__gte=data_inicio_utc,
                            timestamp_data_hora_manual__lte=data_fim_utc,
                        )
                    ).aggregate(Max('numero'))['numero__max']
                elif numeracao == 'U':
                    numero_max = Protocolo.objects.all().aggregate(
                        Max('numero')
                    )['numero__max']

                ultimo_numero_cadastrado = int(numero_max) if numero_max else 0
                if numeracao_nova <= ultimo_numero_cadastrado and numeracao != 'U':
                    msg = "O novo início da numeração de protocolo entrará em vigor na " \
                          "próxima sequência, pois já existe protocolo cadastrado com " \
                          "número superior ou igual ao número inicial definido."
                    messages.warning(self.request, msg)

            return super().form_valid(form)

    class ListView(CrudAux.ListView):

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(reverse('sapl.base:appconfig_create'))

    class DetailView(CrudAux.DetailView):

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(reverse('sapl.base:appconfig_create'))

    class DeleteView(CrudAux.DeleteView):

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(reverse('sapl.base:appconfig_create'))


class SaplSearchView(SearchView):
    results_per_page = 10

    def __init__(self, template=None, load_all=True, form_class=None, searchqueryset=None, results_per_page=None):
        super().__init__(
            template=template,
            load_all=load_all,
            form_class=SaplSearchForm,
            searchqueryset=None,
            results_per_page=results_per_page
        )

    def get_context(self):
        context = super(SaplSearchView, self).get_context()

        data = self.request.GET or self.request.POST
        data = data.copy()

        if 'models' in self.request.GET:
            models = self.request.GET.getlist('models')
        else:
            models = []

        context['models'] = ''
        context['is_paginated'] = True  

        page_obj = context['page']
        context['page_obj'] = page_obj
        paginator = context['paginator']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        if 'page' in data:
            del data['page']

        context['filter_url'] = (
            '&' + data.urlencode()) if len(data) > 0 else ''

        for m in models:
            context['models'] = context['models'] + '&models=' + m

        return context


class AlterarSenha(FormView):
    from sapl.settings import LOGIN_URL

    form_class = AlterarSenhaForm
    template_name = 'base/alterar_senha.html'
    success_url = LOGIN_URL

    def get_initial(self):
        initial = super(AlterarSenha, self).get_initial()
        initial['username'] = self.request.user
        return initial

    def form_valid(self, form):
        new_password = form.cleaned_data['new_password1']

        user = self.request.user
        user.set_password(new_password)
        user.save()

        return super().form_valid(form)


STATIC_LOGO = os.path.join(settings.STATIC_URL, 'img/logo.png')


class LogotipoView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        casa = get_casalegislativa()
        logo = casa and casa.logotipo and casa.logotipo.name
        return os.path.join(settings.MEDIA_URL, logo) if logo else STATIC_LOGO


def filtro_campos(dicionario):

    chaves_desejadas = ['ementa',
                        'ano',
                        'numero',
                        'em_tramitacao',
                        'data_apresentacao',
                        'apelido',
                        'indexacao',
                        'data_publicacao',
                        'data',
                        'data_vigencia']
    del_list = []
    for key in dicionario.keys():
        if key not in chaves_desejadas:
            del_list = del_list + [key]

    for key in del_list:
        del dicionario[key]

    return dicionario


def pesquisa_textual(request):

    if 'q' not in request.GET:
        return JsonResponse({'total': 0,
                             'resultados': []})

    results = SearchQuerySet().filter(content=request.GET['q'])
    json_dict = {
        'total': results.count(),
        'parametros': request.GET['q'],
        'resultados': [],
    }

    for e in results:

        sec_dict = {}
        try:
            sec_dict['pk'] = e.object.pk
        except:
            # Index and db are out of sync. Object has been deleted from
            # database
            continue
        dici = filtro_campos(e.object.__dict__)
        sec_dict['objeto'] = str(dici)
        sec_dict['text'] = str(e.object.ementa)

        sec_dict['model'] = str(type(e.object))

        json_dict['resultados'].append(sec_dict)

    return JsonResponse(json_dict)


class RelatorioHistoricoTramitacaoAdmView(RelatorioMixin, FilterView):
    model = DocumentoAdministrativo
    filterset_class = RelatorioHistoricoTramitacaoAdmFilterSet
    template_name = 'base/RelatorioHistoricoTramitacaoAdm_filter.html'
    relatorio = relatorio_historico_tramitacao_adm

    def get_context_data(self, **kwargs):
        context = super(RelatorioHistoricoTramitacaoAdmView,
                        self).get_context_data(**kwargs)
        context['title'] = _(
            'Histórico de Tramitações de Documento Administrativo')
        if not self.filterset.form.is_valid():
            return context
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)
        context['data_tramitacao'] = (self.request.GET['tramitacaoadministrativo__data_tramitacao_0'] + ' - ' +
                                      self.request.GET['tramitacaoadministrativo__data_tramitacao_1'])
        if self.request.GET['tipo']:
            tipo = self.request.GET['tipo']
            context['tipo'] = (
                str(TipoDocumentoAdministrativo.objects.get(id=tipo)))
        else:
            context['tipo'] = ''

        if self.request.GET['tramitacaoadministrativo__status']:
            tramitacao_status = self.request.GET['tramitacaoadministrativo__status']
            context['tramitacaoadministrativo__status'] = (
                str(StatusTramitacaoAdministrativo.objects.get(id=tramitacao_status)))
        else:
            context['tramitacaoadministrativo__status'] = ''

        if self.request.GET['tramitacaoadministrativo__unidade_tramitacao_local']:
            context['tramitacaoadministrativo__unidade_tramitacao_local'] = \
                (str(UnidadeTramitacao.objects.get(
                    id=self.request.GET['tramitacaoadministrativo__unidade_tramitacao_local'])))
        else:
            context['tramitacaoadministrativo__unidade_tramitacao_local'] = ''

        if self.request.GET['tramitacaoadministrativo__unidade_tramitacao_destino']:
            context['tramitacaoadministrativo__unidade_tramitacao_destino'] = \
                (str(UnidadeTramitacao.objects.get(
                    id=self.request.GET['tramitacaoadministrativo__unidade_tramitacao_destino'])))
        else:
            context['tramitacaoadministrativo__unidade_tramitacao_destino'] = ''

        return context


class RelatorioNormasPorAutorView(RelatorioMixin, FilterView):
    model = NormaJuridica
    filterset_class = RelatorioNormasPorAutorFilterSet
    template_name = 'base/RelatorioNormasPorAutor_filter.html'
    relatorio = relatorio_normas_por_autor

    def get_filterset_kwargs(self, filterset_class):
        super().get_filterset_kwargs(filterset_class)
        kwargs = {'data': self.request.GET or None}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Normas por Autor')
        if not self.filterset.form.is_valid():
            return context

        qtdes = {}
        for tipo in TipoNormaJuridica.objects.all():
            qs = context['object_list']
            qtde = len(qs.filter(tipo_id=tipo.id))
            if qtde > 0:
                qtdes[tipo] = qtde
        context['qtdes'] = qtdes

        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)
        if self.request.GET['tipo']:
            tipo = int(self.request.GET['tipo'])
            context['tipo'] = (
                str(TipoNormaJuridica.objects.get(id=tipo)))
        else:
            context['tipo'] = ''

        if self.request.GET['autorianorma__autor']:
            autor = int(self.request.GET['autorianorma__autor'])
            context['autor'] = (str(Autor.objects.get(id=autor)))
        else:
            context['autor'] = ''
        context['periodo'] = (
            self.request.GET['data_0'] +
            ' - ' + self.request.GET['data_1'])

        return context
