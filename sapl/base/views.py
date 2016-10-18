
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django_filters.views import FilterView


from sapl.base.forms import AutorForm, TipoAutorForm, AutorFormForAdmin

from sapl.base.models import Autor, TipoAutor
from sapl.crud.base import CrudAux
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.sessao.models import OrdemDia, SessaoPlenaria

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
        list_field_names = ['tipo', 'nome', 'user__username']

    class DeleteView(CrudAux.DeleteView):

        def delete(self, *args, **kwargs):
            self.object = self.get_object()

            # FIXME melhorar captura de grupo de Autor, levando em conta trad
            grupo = Group.objects.filter(name='Autor')[0]
            self.object.user.groups.remove(grupo)

            return CrudAux.DeleteView.delete(self, *args, **kwargs)

    class UpdateView(CrudAux.UpdateView):
        layout_key = None
        form_class = AutorForm

        def get(self, request, *args, **kwargs):
            if request.user.is_superuser:
                self.form_class = AutorFormForAdmin
            return CrudAux.UpdateView.get(self, request, *args, **kwargs)

        def get_success_url(self):

            # FIXME try except - testar envio de emails

            pk_autor = self.object.id
            try:
                kwargs = {}
                user = self.object.user

                if user.is_active:
                    return reverse('sapl.base:autor_detail',
                                   kwargs={'pk': pk_autor})

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
                    reverse('sapl.materia:confirmar_email', kwargs=kwargs))
                remetente = [settings.EMAIL_SEND_USER]
                destinatario = [user.email]
                send_mail(assunto, mensagem, remetente, destinatario,
                          fail_silently=False)
            except:
                pass
            return reverse('sapl.base:autor_detail',
                           kwargs={'pk': pk_autor})

    class CreateView(CrudAux.CreateView):
        form_class = AutorForm
        layout_key = None

        def get(self, request, *args, **kwargs):
            if request.user.is_superuser:
                self.form_class = AutorFormForAdmin
            return CrudAux.CreateView.get(self, request, *args, **kwargs)

        def get_success_url(self):
            pk_autor = self.object.id
            try:
                # FIXME try except - testar envio de emails
                kwargs = {}
                user = self.object.user
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
                    reverse('sapl.materia:confirmar_email', kwargs=kwargs))
                remetente = settings.EMAIL_SEND_USER
                destinatario = [user.email]
                send_mail(assunto, mensagem, remetente, destinatario,
                          fail_silently=False)
            except:
                pass

            return reverse('sapl.base:autor_detail',
                           kwargs={'pk': pk_autor})


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
        return context


class RelatorioPresencaSessaoView(FilterView):
    model = SessaoPlenaria
    filterset_class = RelatorioPresencaSessaoFilterSet
    template_name = 'base/RelatorioPresencaSessao_filter.html'

    def calcular_porcentagem_presenca(self,
                                      parlamentares,
                                      total_sessao,
                                      total_ordemdia):
        for p in parlamentares:
            p.sessao_porc = round(p.sessao_count * 100 / total_sessao, 1)
            p.ordemdia_porc = round(p.ordemdia_count * 100 / total_ordemdia, 1)
        return parlamentares

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
            param1 = {'presencaordemdia__%s' % sufixo: _range}
            param2 = {'sessaoplenariapresenca__%s' % sufixo: _range}

            pls = Parlamentar.objects.filter(
                (Q(**param1) | Q(presencaordemdia__isnull=True)) &
                (Q(**param2) | Q(sessaoplenariapresenca__isnull=True))
            ).annotate(
                sessao_count=Count(
                    'sessaoplenariapresenca__sessao_plenaria',
                    distinct=True),
                ordemdia_count=Count(
                    'presencaordemdia__sessao_plenaria',
                    distinct=True),
                sessao_porc=Count(0),
                ordemdia_porc=Count(0)
            ).exclude(
                sessao_count=0,
                ordemdia_count=0)

            total_ordemdia = OrdemDia.objects.order_by(
                'sessao_plenaria').filter(**param0).distinct(
                'sessao_plenaria').count()

            self.calcular_porcentagem_presenca(
                pls,
                context['object_list'].count(),
                total_ordemdia)

            context['total_ordemdia'] = total_ordemdia
            context['total_sessao'] = context['object_list'].count()
            context['parlamentares'] = pls
            context['periodo'] = (
                self.request.GET['data_inicio_0'] +
                ' - ' + self.request.GET['data_inicio_1'])
        # =====================================================================
        qr = self.request.GET.copy()
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''
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

        return context


class RelatorioMateriasPorAnoAutorTipoView(FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioMateriasPorAnoAutorTipoFilterSet
    template_name = 'base/RelatorioMateriasPorAnoAutorTipo_filter.html'

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

        return context


class CasaLegislativaCrud(CrudAux):
    model = CasaLegislativa

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = ['codigo', 'nome', 'sigla']
        form_class = CasaLegislativaForm

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
