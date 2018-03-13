from django.conf import settings
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import string_concat
from django.views.generic import (CreateView, DeleteView, DetailView, FormView,
                                  ListView, UpdateView)
from django.views.generic.base import TemplateView
from django_filters.views import FilterView
from haystack.views import SearchView

from sapl.base.forms import AutorForm, AutorFormForAdmin, TipoAutorForm
from sapl.base.models import Autor, TipoAutor
from sapl.crud.base import CrudAux, make_pagination
from sapl.materia.models import (Autoria, MateriaLegislativa,
                                 TipoMateriaLegislativa)
from sapl.sessao.models import (PresencaOrdemDia, SessaoPlenaria,
                                SessaoPlenariaPresenca)
from sapl.utils import (parlamentares_ativos, sapl_logger,
                        show_results_filter_set)

from .forms import (AlterarSenhaForm, CasaLegislativaForm,
                    ConfiguracoesAppForm, RelatorioAtasFilterSet,
                    RelatorioDataFimPrazoTramitacaoFilterSet,
                    RelatorioHistoricoTramitacaoFilterSet,
                    RelatorioMateriasPorAnoAutorTipoFilterSet,
                    RelatorioMateriasPorAutorFilterSet,
                    RelatorioMateriasTramitacaoilterSet,
                    RelatorioPresencaSessaoFilterSet, UsuarioCreateForm,
                    UsuarioEditForm)
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
    help_topic = 'tipo-autor'

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ['descricao']
        form_class = TipoAutorForm

        @property
        def verbose_name(self):
            vn = super().verbose_name
            vn = string_concat(vn, ' ', _('Externo ao SAPL'))
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

        context['show_results'] = show_results_filter_set(qr)

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
        # if 'salvar' not in self.request.GET:
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

        context['show_results'] = show_results_filter_set(qr)

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

        context['show_results'] = show_results_filter_set(qr)

        return context


class RelatorioDataFimPrazoTramitacaoView(FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioDataFimPrazoTramitacaoFilterSet
    template_name = 'base/RelatorioDataFimPrazoTramitacao_filter.html'

    def get_context_data(self, **kwargs):
        context = super(RelatorioDataFimPrazoTramitacaoView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Fim de Prazo de Tramitações')
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

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

        context['show_results'] = show_results_filter_set(qr)

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

        context['show_results'] = show_results_filter_set(qr)

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

        context['show_results'] = show_results_filter_set(qr)

        return context


class ListarUsuarioView(PermissionRequiredMixin, ListView):
    model = get_user_model()
    template_name = 'auth/user_list.html'
    context_object_name = 'user_list'
    permission_required = ('base.list_appconfig',)
    paginate_by = 10

    def get_queryset(self):
        qs = super(ListarUsuarioView, self).get_queryset()
        return qs.order_by('username')

    def get_context_data(self, **kwargs):
        context = super(ListarUsuarioView, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        context['NO_ENTRIES_MSG'] = 'Nenhum usuário cadastrado.'
        return context


class CreateUsuarioView(PermissionRequiredMixin, CreateView):
    model = get_user_model()
    form_class = UsuarioCreateForm
    success_message = 'Usuário criado com sucesso'
    permission_required = ('base.add_appconfig',)

    def get_success_url(self):
        return reverse('sapl.base:user_list')

    def form_valid(self, form):

        data = form.cleaned_data

        new_user = get_user_model().objects.create(username=data['username'], email=data['email'])
        new_user.first_name = data['firstname']
        new_user.last_name = data['lastname']
        new_user.set_password(data['password1'])
        new_user.is_superuser = False
        new_user.is_staff = False
        new_user.save()

        groups = Group.objects.filter(id__in=data['roles'])
        for g in groups:
            g.user_set.add(new_user)

        return HttpResponseRedirect(self.get_success_url())


class DeleteUsuarioView(PermissionRequiredMixin, DeleteView):

    model = get_user_model()
    permission_required = ('base.delete_appconfig',)

    def get_success_url(self):
        return reverse('sapl.base:user_list')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(DeleteUsuarioView, self).get_queryset()
        return qs.filter(id=self.kwargs['pk'])


class EditUsuarioView(PermissionRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UsuarioEditForm
    success_message = 'Usuário editado com sucesso'
    permission_required = ('base.change_appconfig',)

    def get_success_url(self):
        return reverse('sapl.base:user_list')

    def get_initial(self):
        initial = super(EditUsuarioView, self).get_initial()

        user = get_user_model().objects.get(id=self.kwargs['pk'])
        roles = [str(g.id) for g in user.groups.all()]
        initial['roles'] = roles
        initial['user_active'] = user.is_active

        return initial

    def form_valid(self, form):

        user = form.save(commit=False)
        data = form.cleaned_data

        # new_user.first_name = data['firstname']
        # new_user.last_name = data['lastname']

        if data['password1']:
            user.set_password(data['password1'])

        if data['user_active'] == 'True' and not user.is_active:
            user.is_active = True
        elif data['user_active'] == 'False' and user.is_active:
            user.is_active = False

        user.save()

        for g in user.groups.all():
            g.user_set.remove(user)

        groups = Group.objects.filter(id__in=data['roles'])
        for g in groups:
            g.user_set.add(user)

        return super(EditUsuarioView, self).form_valid(form)


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

    def get_template_names(self):
        topico = self.kwargs['topic']
        try:
            get_template('ajuda/%s.html' % topico)
        except TemplateDoesNotExist:
            raise Http404()
        return ['ajuda/%s.html' % topico]


class AppConfigCrud(CrudAux):
    model = AppConfig

    class BaseMixin(CrudAux.BaseMixin):
        form_class = ConfiguracoesAppForm

        list_url = ''
        create_url = ''

    class CreateView(CrudAux.CreateView):

        def get(self, request, *args, **kwargs):
            app_config = AppConfig.objects.first()

            if not app_config:
                app_config = AppConfig()
                app_config.save()

            return HttpResponseRedirect(
                reverse('sapl.base:appconfig_update',
                        kwargs={'pk': app_config.pk}))

        def post(self, request, *args, **kwargs):
            return self.get(request, *args, **kwargs)

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
