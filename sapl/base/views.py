
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django_filters.views import FilterView
from haystack.views import SearchView

from sapl.base.forms import AutorForm, AutorFormForAdmin, TipoAutorForm
from sapl.base.models import Autor, TipoAutor
from sapl.crud.base import CrudAux
from sapl.materia.models import (Autoria, MateriaLegislativa,
                                 TipoMateriaLegislativa)
from sapl.sessao.models import (PresencaOrdemDia, SessaoPlenaria,
                                SessaoPlenariaPresenca)
from sapl.utils import parlamentares_ativos, sapl_logger

from .forms import (CasaLegislativaForm, ConfiguracoesAppForm,
                    RelatorioAtasFilterSet,
                    RelatorioHistoricoTramitacaoFilterSet,
                    RelatorioMateriasPorAnoAutorTipoFilterSet,
                    RelatorioMateriasPorAutorFilterSet,
                    RelatorioMateriasTramitacaoilterSet,
                    RelatorioPresencaSessaoFilterSet)
from .models import AppConfig, CasaLegislativa


def get_casalegislativa():
    return CasaLegislativa.objects.first()


class ConfirmarEmailView(TemplateView):
    template_name = "email/confirma.html"

    def get(self, request, *args, **kwargs):
        uid = urlsafe_base64_decode(self.kwargs['uidb64'])
        user = get_user_model().objects.get(id=uid)
        user.is_active = True
        user.save()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class TipoAutorCrud(CrudAux):
    model = TipoAutor
    help_path = 'tipo-autor'

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ['descricao', 'content_type']
        form_class = TipoAutorForm


class AutorCrud(CrudAux):
    model = Autor
    help_path = 'autor'

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ['tipo', 'nome', 'user']

    class DeleteView(CrudAux.DeleteView):

        def delete(self, *args, **kwargs):
            self.object = self.get_object()

            if self.object.user:
                # FIXME melhorar captura de grupo de Autor, levando em conta
                # trad
                grupo = Group.objects.filter(name='Autor')[0]
                self.object.user.groups.remove(grupo)

            return CrudAux.DeleteView.delete(self, *args, **kwargs)

    class UpdateView(CrudAux.UpdateView):
        layout_key = None
        form_class = AutorForm

        def form_valid(self, form):
            # devido a implement do form o form_valid do Crud deve ser pulado
            return super(CrudAux.UpdateView, self).form_valid(form)

        def post(self, request, *args, **kwargs):
            if request.user.is_superuser:
                self.form_class = AutorFormForAdmin
            return CrudAux.UpdateView.post(self, request, *args, **kwargs)

        def get(self, request, *args, **kwargs):
            if request.user.is_superuser:
                self.form_class = AutorFormForAdmin
            return CrudAux.UpdateView.get(self, request, *args, **kwargs)

        def get_success_url(self):
            pk_autor = self.object.id
            url_reverse = reverse('sapl.base:autor_detail',
                                  kwargs={'pk': pk_autor})
            try:
                kwargs = {}
                user = self.object.user

                if not user:
                    return url_reverse

                kwargs['token'] = default_token_generator.make_token(user)
                kwargs['uidb64'] = urlsafe_base64_encode(force_bytes(user.pk))
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
                remetente = [settings.EMAIL_SEND_USER]
                destinatario = [user.email]
                send_mail(assunto, mensagem, remetente, destinatario,
                          fail_silently=False)
            except:
                sapl_logger.error(
                    _('Erro no envio de email na edição de Autores.'))
            return url_reverse

    class CreateView(CrudAux.CreateView):
        form_class = AutorForm
        layout_key = None

        def post(self, request, *args, **kwargs):
            if request.user.is_superuser:
                self.form_class = AutorFormForAdmin
            return CrudAux.CreateView.post(self, request, *args, **kwargs)

        def get(self, request, *args, **kwargs):
            if request.user.is_superuser:
                self.form_class = AutorFormForAdmin
            return CrudAux.CreateView.get(self, request, *args, **kwargs)

        def get_success_url(self):
            pk_autor = self.object.id
            url_reverse = reverse('sapl.base:autor_detail',
                                  kwargs={'pk': pk_autor})
            try:
                kwargs = {}
                user = self.object.user

                if not user:
                    return url_reverse

                kwargs['token'] = default_token_generator.make_token(user)
                kwargs['uidb64'] = urlsafe_base64_encode(force_bytes(user.pk))
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
                remetente = [settings.EMAIL_SEND_USER]
                destinatario = [user.email]
                send_mail(assunto, mensagem, remetente, destinatario,
                          fail_silently=False)
            except:
                sapl_logger.error(
                    _('Erro no envio de email na criação de Autores.'))
            return url_reverse


class RelatorioAtasView(FilterView):
    model = SessaoPlenaria
    filterset_class = RelatorioAtasFilterSet
    template_name = 'base/RelatorioAtas_filter.html'

    def get_context_data(self, **kwargs):
        context = super(RelatorioAtasView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Atas das Sessões Plenárias')

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        context['object_list'] = context['object_list'].exclude(upload_ata='')
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        query_params = set(qr.keys())
        if ((len(query_params) == 1 and 'iframe' in query_params) or
                len(query_params) == 0):
            context['show_results'] = False
        else:
            context['show_results'] = True

        return context


class RelatorioPresencaSessaoView(FilterView):
    model = SessaoPlenaria
    filterset_class = RelatorioPresencaSessaoFilterSet
    template_name = 'base/RelatorioPresencaSessao_filter.html'

    def get_context_data(self, **kwargs):
        context = super(RelatorioPresencaSessaoView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Presença dos parlamentares nas sessões')

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        # =====================================================================
        if 'salvar' in self.request.GET:
            where = context['object_list'].query.where
            _range = where.children[0].rhs

            sufixo = 'sessao_plenaria__data_inicio__range'
            param0 = {'%s' % sufixo: _range}

            # Parlamentares com Mandato no intervalo de tempo (Ativos)
            parlamentares_qs = parlamentares_ativos(
                _range[0], _range[1]).order_by('nome_parlamentar')
            parlamentares_id = parlamentares_qs.values_list(
                'id', flat=True)

            # Presenças de cada Parlamentar em Sessões
            presenca_sessao = SessaoPlenariaPresenca.objects.filter(
                parlamentar_id__in=parlamentares_id,
                sessao_plenaria__data_inicio__range=_range).values_list(
                'parlamentar_id').annotate(
                sessao_count=Count('id'))

            # Presenças de cada Ordem do Dia
            presenca_ordem = PresencaOrdemDia.objects.filter(
                parlamentar_id__in=parlamentares_id,
                sessao_plenaria__data_inicio__range=_range).values_list(
                'parlamentar_id').annotate(
                sessao_count=Count('id'))

            total_ordemdia = PresencaOrdemDia.objects.filter(
                **param0).distinct('sessao_plenaria__id').order_by(
                'sessao_plenaria__id').count()

            total_sessao = context['object_list'].count()

            # Completa o dicionario as informacoes parlamentar/sessao/ordem
            parlamentares_presencas = []
            for i, p in enumerate(parlamentares_qs):
                parlamentares_presencas.append({
                    'parlamentar': p,
                    'sessao_porc': 0,
                    'ordemdia_porc': 0
                })
                try:
                    sessao_count = presenca_sessao.get(parlamentar_id=p.id)[1]
                except ObjectDoesNotExist:
                    sessao_count = 0
                try:
                    ordemdia_count = presenca_ordem.get(parlamentar_id=p.id)[1]
                except ObjectDoesNotExist:
                    ordemdia_count = 0

                parlamentares_presencas[i].update({
                    'sessao_count': sessao_count,
                    'ordemdia_count': ordemdia_count
                })

                if total_sessao != 0:
                    parlamentares_presencas[i].update(
                        {'sessao_porc': round(
                            sessao_count * 100 / total_sessao, 2)})
                if total_ordemdia != 0:
                    parlamentares_presencas[i].update(
                        {'ordemdia_porc': round(
                            ordemdia_count * 100 / total_ordemdia, 2)})

            context['date_range'] = _range
            context['total_ordemdia'] = total_ordemdia
            context['total_sessao'] = context['object_list'].count()
            context['parlamentares'] = parlamentares_presencas
            context['periodo'] = (
                self.request.GET['data_inicio_0'] +
                ' - ' + self.request.GET['data_inicio_1'])
        # =====================================================================
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        query_params = set(qr.keys())
        if ((len(query_params) == 1 and 'iframe' in query_params) or
                len(query_params) == 0):
            context['show_results'] = False
        else:
            context['show_results'] = True

        return context


class RelatorioHistoricoTramitacaoView(FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioHistoricoTramitacaoFilterSet
    template_name = 'base/RelatorioHistoricoTramitacao_filter.html'

    def get_context_data(self, **kwargs):
        context = super(RelatorioHistoricoTramitacaoView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Histórico de Tramitações')
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        query_params = set(qr.keys())
        if ((len(query_params) == 1 and 'iframe' in query_params) or
                len(query_params) == 0):
            context['show_results'] = False
        else:
            context['show_results'] = True

        return context


class RelatorioMateriasTramitacaoView(FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioMateriasTramitacaoilterSet
    template_name = 'base/RelatorioMateriasPorTramitacao_filter.html'

    def get_context_data(self, **kwargs):
        context = super(RelatorioMateriasTramitacaoView,
                        self).get_context_data(**kwargs)

        context['title'] = _('Matérias por Ano, Autor e Tipo')

        qs = context['object_list']
        qs = qs.filter(em_tramitacao=True)
        context['object_list'] = qs

        qtdes = {}
        for tipo in TipoMateriaLegislativa.objects.all():
            qs = context['object_list']
            qtde = len(qs.filter(tipo_id=tipo.id))
            if qtde > 0:
                qtdes[tipo] = qtde
        context['qtdes'] = qtdes

        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        query_params = set(qr.keys())
        if ((len(query_params) == 1 and 'iframe' in query_params) or
                len(query_params) == 0):
            context['show_results'] = False
        else:
            context['show_results'] = True

        return context


class RelatorioMateriasPorAnoAutorTipoView(FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioMateriasPorAnoAutorTipoFilterSet
    template_name = 'base/RelatorioMateriasPorAnoAutorTipo_filter.html'

    def get_materias_autor_ano(self, ano):

        autorias = Autoria.objects.filter(materia__ano=ano).values(
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

        qtdes = {}
        for tipo in TipoMateriaLegislativa.objects.all():
            qs = kwargs['object_list']
            qtde = len(qs.filter(tipo_id=tipo.id))
            if qtde > 0:
                qtdes[tipo] = qtde
        context['qtdes'] = qtdes

        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        query_params = set(qr.keys())
        if ((len(query_params) == 1 and 'iframe' in query_params) or
                len(query_params) == 0):
            context['show_results'] = False
        else:
            context['show_results'] = True

        if 'ano' in self.request.GET and self.request.GET['ano']:
            ano = int(self.request.GET['ano'])
            context['relatorio'] = self.get_materias_autor_ano(ano)
        else:
            context['relatorio'] = []

        return context


class RelatorioMateriasPorAutorView(FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioMateriasPorAutorFilterSet
    template_name = 'base/RelatorioMateriasPorAutor_filter.html'

    def get_filterset_kwargs(self, filterset_class):
        super(RelatorioMateriasPorAutorView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(RelatorioMateriasPorAutorView,
                        self).get_context_data(**kwargs)

        context['title'] = _('Matérias por Autor')

        qtdes = {}
        for tipo in TipoMateriaLegislativa.objects.all():
            qs = kwargs['object_list']
            qtde = len(qs.filter(tipo_id=tipo.id))
            if qtde > 0:
                qtdes[tipo] = qtde
        context['qtdes'] = qtdes

        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        query_params = set(qr.keys())
        if ((len(query_params) == 1 and 'iframe' in query_params) or
                len(query_params) == 0):
            context['show_results'] = False
        else:
            context['show_results'] = True

        return context


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


class HelpView(PermissionRequiredMixin, TemplateView):
    # XXX treat non existing template as a 404!!!!

    def get_template_names(self):
        return ['ajuda/%s.html' % self.kwargs['topic']]


class AppConfigCrud(CrudAux):
    model = AppConfig

    class BaseMixin(CrudAux.BaseMixin):
        form_class = ConfiguracoesAppForm

        @property
        def list_url(self):
            return ''

        @property
        def create_url(self):
            return ''

    class CreateView(CrudAux.CreateView):

        def get(self, request, *args, **kwargs):
            app_config = AppConfig.objects.last()
            if app_config:
                return HttpResponseRedirect(
                    reverse('sapl.base:appconfig_update',
                            kwargs={'pk': app_config.pk}))
            else:
                self.object = None
                return super(CrudAux.CreateView, self).get(
                    request, *args, **kwargs)

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

    def get_context(self):
        context = super(SaplSearchView, self).get_context()

        if 'models' in self.request.GET:
            models = self.request.GET.getlist('models')
        else:
            models = []

        context['models'] = ''

        for m in models:
            context['models'] = context['models'] + '&models=' + m

        return context
