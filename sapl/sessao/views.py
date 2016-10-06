from datetime import datetime
from re import sub

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse
from django.forms.utils import ErrorList
from django.http import JsonResponse
from django.http.response import HttpResponseRedirect
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, TemplateView
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django_filters.views import FilterView
from rest_framework import generics

from sapl.base.models import AppConfig as AppsAppConfig
from sapl.crud.base import (RP_DETAIL, RP_LIST, Crud, CrudAux,
                            MasterDetailCrud,
                            PermissionRequiredForAppCrudMixin, make_pagination)
from sapl.materia.forms import pega_ultima_tramitacao
from sapl.materia.models import (Autoria, DocumentoAcessorio,
                                 TipoMateriaLegislativa, Tramitacao)
from sapl.materia.views import MateriaLegislativaPesquisaView
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import (Legislatura, Parlamentar,
                                       SessaoLegislativa)
from sapl.sessao.apps import AppConfig
from sapl.sessao.forms import ExpedienteMateriaForm, OrdemDiaForm
from sapl.sessao.serializers import SessaoPlenariaSerializer
from sapl.utils import permission_required_for_app

from .forms import (AdicionarVariasMateriasFilterSet, ExpedienteForm,
                    ListMateriaForm, MesaForm, OradorExpedienteForm,
                    OradorForm, PautaSessaoFilterSet, PresencaForm,
                    SessaoPlenariaFilterSet, VotacaoEditForm, VotacaoForm,
                    VotacaoNominalForm)
from .models import (Bancada, Bloco, CargoBancada, CargoMesa,
                     ExpedienteMateria, ExpedienteSessao, IntegranteMesa,
                     MateriaLegislativa, Orador, OradorExpediente, OrdemDia,
                     PresencaOrdemDia, RegistroVotacao, SessaoPlenaria,
                     SessaoPlenariaPresenca, TipoExpediente,
                     TipoResultadoVotacao, TipoSessaoPlenaria, VotoParlamentar)


TipoSessaoCrud = CrudAux.build(TipoSessaoPlenaria, 'tipo_sessao_plenaria')
TipoExpedienteCrud = CrudAux.build(TipoExpediente, 'tipo_expediente')
CargoBancadaCrud = CrudAux.build(CargoBancada, '')

BlocoCrud = CrudAux.build(
    Bloco, '', list_field_names=['nome', 'data_criacao', 'partidos'])
BancadaCrud = CrudAux.build(
    Bancada, '', list_field_names=['nome', 'legislatura'])
TipoResultadoVotacaoCrud = CrudAux.build(
    TipoResultadoVotacao, 'tipo_resultado_votacao')


def reordernar_materias_expediente(request, pk):
    expedientes = ExpedienteMateria.objects.filter(
        sessao_plenaria_id=pk)
    exp_num = 1
    for e in expedientes:
        e.numero_ordem = exp_num
        e.save()
        exp_num += 1

    return HttpResponseRedirect(
        reverse('sapl.sessao:expedientemateria_list', kwargs={'pk': pk}))


def reordernar_materias_ordem(request, pk):
    ordens = OrdemDia.objects.filter(
        sessao_plenaria_id=pk)
    ordem_num = 1
    for o in ordens:
        o.numero_ordem = ordem_num
        o.save()
        ordem_num += 1

    return HttpResponseRedirect(
        reverse('sapl.sessao:ordemdia_list', kwargs={'pk': pk}))


def abrir_votacao_expediente_view(request, pk, spk):
    existe_votacao_aberta = ExpedienteMateria.objects.filter(
        sessao_plenaria_id=spk, votacao_aberta=True
    ).exists()
    if existe_votacao_aberta:
        msg = _('Já existe uma matéria com votação aberta. Para abrir '
                'outra, termine ou feche a votação existente.')
        raise ValidationError(msg)
    else:
        expediente = ExpedienteMateria.objects.get(id=pk)
        expediente.votacao_aberta = True
        expediente.save()
    return HttpResponseRedirect(
        reverse('sapl.sessao:expedientemateria_list', kwargs={'pk': spk}))


def abrir_votacao_ordem_view(request, pk, spk):
    existe_votacao_aberta = OrdemDia.objects.filter(
        sessao_plenaria_id=spk, votacao_aberta=True
    ).exists()
    if existe_votacao_aberta:
        msg = _('Já existe uma matéria com votação aberta. Para abrir '
                'outra, termine ou feche a votação existente.')
        raise ValidationError(msg)
    else:
        ordem = OrdemDia.objects.get(id=pk)
        ordem.votacao_aberta = True
        ordem.save()
    return HttpResponseRedirect(
        reverse('sapl.sessao:ordemdia_list', kwargs={'pk': spk}))


class MateriaOrdemDiaCrud(MasterDetailCrud):
    model = OrdemDia
    parent_field = 'sessao_plenaria'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['numero_ordem', 'materia', 'observacao',
                            'resultado']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = OrdemDiaForm

        def get_success_url(self):
            return reverse('sapl.sessao:ordemdia_list',
                           kwargs={'pk': self.kwargs['pk']})

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = OrdemDiaForm

        def get_initial(self):
            self.initial['tipo_materia'] = self.object.materia.tipo.id
            self.initial['numero_materia'] = self.object.materia.numero
            self.initial['ano_materia'] = self.object.materia.ano
            return self.initial

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return 'OrdemDiaDetail'

    class ListView(MasterDetailCrud.ListView):
        ordering = ['numero_ordem', 'materia', 'resultado']

        def get_rows(self, object_list):
            for obj in object_list:
                if not obj.resultado:
                    if obj.votacao_aberta:
                        url = ''
                        if obj.tipo_votacao == 1:
                            url = reverse('sapl.sessao:votacaosimbolica',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})
                        elif obj.tipo_votacao == 2:
                            url = reverse('sapl.sessao:votacaonominal',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})
                        elif obj.tipo_votacao == 3:
                            url = reverse('sapl.sessao:votacaosecreta',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})
                        if self.request.user.has_module_perms(AppConfig.label):
                            btn_registrar = '''
                            <a href="%s"
                               class="btn btn-primary"
                               role="button">Registrar Votação</a>''' % (
                                url)
                            obj.resultado = btn_registrar
                        else:
                            obj.resultado = '''Não há resultado'''
                    else:
                        url = reverse('sapl.sessao:abrir_votacao', kwargs={
                            'pk': obj.pk, 'spk': obj.sessao_plenaria_id})

                        if self.request.user.has_module_perms(AppConfig.label):
                            btn_abrir = '''
                                Matéria não votada<br />
                                <a href="%s"
                                   class="btn btn-primary"
                                   role="button">Abrir Votação</a>''' % (url)
                            obj.resultado = btn_abrir
                        else:
                            obj.resultado = '''Não há resultado'''
                else:
                    if self.request.user.has_module_perms(AppConfig.label):
                        url = ''
                        if obj.tipo_votacao == 1:
                            url = reverse('sapl.sessao:votacaosimbolicaedit',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})
                        elif obj.tipo_votacao == 2:
                            url = reverse('sapl.sessao:votacaonominaledit',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})
                        elif obj.tipo_votacao == 3:
                            url = reverse('sapl.sessao:votacaosecretaedit',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})
                        obj.resultado = '<a href="%s">%s</a>' % (url,
                                                                 obj.resultado)
                    else:
                        obj.resultado = '%s' % (obj.resultado)

            return [self._as_row(obj) for obj in object_list]


def recuperar_materia(request):
    tipo = TipoMateriaLegislativa.objects.get(pk=request.GET['tipo_materia'])
    numero = request.GET['numero_materia']
    ano = request.GET['ano_materia']

    try:
        materia = MateriaLegislativa.objects.get(tipo=tipo,
                                                 ano=ano,
                                                 numero=numero)
        response = JsonResponse({'ementa': materia.ementa,
                                 'id': materia.id})
    except ObjectDoesNotExist:
        response = JsonResponse({'ementa': '', 'id': 0})

    return response


class ExpedienteMateriaCrud(MasterDetailCrud):
    model = ExpedienteMateria
    parent_field = 'sessao_plenaria'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['numero_ordem', 'materia',
                            'observacao', 'resultado']

    class ListView(MasterDetailCrud.ListView):
        ordering = ['numero_ordem', 'materia', 'resultado']

        def get_rows(self, object_list):
            for obj in object_list:
                if not obj.resultado:
                    if obj.votacao_aberta:
                        url = ''
                        if obj.tipo_votacao == 1:
                            url = reverse('sapl.sessao:votacaosimbolicaexp',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})
                        elif obj.tipo_votacao == 2:
                            url = reverse('sapl.sessao:votacaonominalexp',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})
                        elif obj.tipo_votacao == 3:
                            url = reverse('sapl.sessao:votacaosecretaexp',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})

                        if self.request.user.has_module_perms(AppConfig.label):
                            btn_registrar = '''
                                <a href="%s" class="btn btn-primary"
                                   role="button">
                                   Registrar Votação</a>''' % (url)
                            obj.resultado = btn_registrar
                    else:
                        url = reverse('sapl.sessao:abrir_votacao_exp', kwargs={
                            'pk': obj.pk, 'spk': obj.sessao_plenaria_id})
                        btn_abrir = '''Matéria não votada<br />'''

                        if self.request.user.has_module_perms(AppConfig.label):
                            btn_abrir += '''
                            <a href="%s"
                               class="btn btn-primary"
                               role="button">Abrir Votação</a>''' % (url)

                        obj.resultado = btn_abrir
                else:
                    url = ''

                    if self.request.user.has_module_perms(AppConfig.label):
                        if obj.tipo_votacao == 1:
                            url = reverse(
                                'sapl.sessao:votacaosimbolicaexpedit',
                                kwargs={
                                    'pk': obj.sessao_plenaria_id,
                                    'oid': obj.materia_id,
                                    'mid': obj.pk})
                        elif obj.tipo_votacao == 2:
                            url = reverse('sapl.sessao:votacaonominalexpedit',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})
                        elif obj.tipo_votacao == 3:
                            url = reverse('sapl.sessao:votacaosecretaexpedit',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.materia_id,
                                              'mid': obj.pk})
                        obj.resultado = '<a href="%s">%s</a>' % (url,
                                                                 obj.resultado)
            return [self._as_row(obj) for obj in object_list]

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ExpedienteMateriaForm

        def get_success_url(self):
            return reverse('sapl.sessao:expedientemateria_list',
                           kwargs={'pk': self.kwargs['pk']})

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = ExpedienteMateriaForm

        def get_initial(self):
            self.initial['tipo_materia'] = self.object.materia.tipo.id
            self.initial['numero_materia'] = self.object.materia.numero
            self.initial['ano_materia'] = self.object.materia.ano
            return self.initial

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return 'ExpedienteMateriaDetail'


class OradorCrud(MasterDetailCrud):
    model = ''
    parent_field = 'sessao_plenaria'
    help_path = ''
    public = [RP_LIST, RP_DETAIL]

    class ListView(MasterDetailCrud.ListView):
        ordering = ['numero_ordem', 'parlamentar']


class OradorExpedienteCrud(OradorCrud):
    model = OradorExpediente

    class CreateView(MasterDetailCrud.CreateView):

        form_class = OradorExpedienteForm

        def get_initial(self):
            return {'id_sessao': self.kwargs['pk']}

        def get_success_url(self):
            return reverse('sapl.sessao:oradorexpediente_list',
                           kwargs={'pk': self.kwargs['pk']})


class OradorCrud(OradorCrud):
    model = Orador

    class CreateView(MasterDetailCrud.CreateView):

        form_class = OradorForm

        def get_initial(self):
            return {'id_sessao': self.kwargs['pk']}

        def get_success_url(self):
            return reverse('sapl.sessao:orador_list',
                           kwargs={'pk': self.kwargs['pk']})


def recuperar_numero_sessao(request):
    try:
        sessao = SessaoPlenaria.objects.filter(
            tipo__pk=request.GET['tipo'],
            sessao_legislativa=request.GET['sessao_legislativa']).last()
    except ObjectDoesNotExist:
        response = JsonResponse({'numero': 1})
    else:
        if sessao:
            response = JsonResponse({'numero': sessao.numero + 1})
        else:
            response = JsonResponse({'numero': 1})

    return response


def sessao_legislativa_legislatura_ajax(request):
    try:
        sessao = SessaoLegislativa.objects.filter(
            legislatura=request.GET['legislatura']).order_by('-data_inicio')
    except ObjectDoesNotExist:
        sessao = SessaoLegislativa.objects.all().order_by('-data_inicio')

    lista_sessoes = [(s.id, s.__str__()) for s in sessao]

    return JsonResponse({'sessao_legislativa': lista_sessoes})


class SessaoCrud(Crud):
    model = SessaoPlenaria
    help_path = 'sessao_plenaria'
    public = [RP_DETAIL]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['data_inicio', 'legislatura', 'sessao_legislativa',
                            'tipo']

        @property
        def list_url(self):
            return ''

        @property
        def search_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesquisar_sessao'))

    class ListView(Crud.ListView, RedirectView):

        def get_redirect_url(self, *args, **kwargs):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'pesquisar_sessao'))

        def get(self, request, *args, **kwargs):
            return RedirectView.get(self, request, *args, **kwargs)

    class CreateView(Crud.CreateView):

        @property
        def cancel_url(self):
            return self.search_url

        def get_initial(self):
            legislatura = Legislatura.objects.order_by('-data_inicio')[0]
            return {'legislatura': legislatura}


class SessaoPermissionMixin(PermissionRequiredForAppCrudMixin,
                            FormMixin,
                            DetailView):
    model = SessaoPlenaria
    app_label = AppConfig.label,


class PresencaMixin:

    def get_presencas(self):
        self.object = self.get_object()

        presencas = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id
        )
        presentes = [p.parlamentar for p in presencas]

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                yield (parlamentar, True)
            else:
                yield (parlamentar, False)

    def get_presencas_ordem(self):
        self.object = self.get_object()

        presencas = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id
        )
        presentes = [p.parlamentar for p in presencas]

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                yield (parlamentar, True)
            else:
                yield (parlamentar, False)


class PresencaView(FormMixin, PresencaMixin, DetailView):
    template_name = 'sessao/presenca.html'
    form_class = PresencaForm
    model = SessaoPlenaria

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Presença'), self.object)
        return context

    @method_decorator(permission_required_for_app(AppConfig.label))
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if not self.request.user.has_module_perms(AppConfig.label):
            return self.form_invalid(form)

        if form.is_valid():
            # Pegar os presentes salvos no banco
            presentes_banco = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=self.object.id)

            # Id dos parlamentares presentes
            marcados = request.POST.getlist('presenca')

            # Deletar os que foram desmarcadors
            deletar = set(set(presentes_banco) - set(marcados))
            for d in deletar:
                SessaoPlenariaPresenca.objects.filter(
                    parlamentar_id=d.parlamentar_id).delete()

            for p in marcados:
                sessao = SessaoPlenariaPresenca()
                sessao.sessao_plenaria = self.object
                sessao.parlamentar = Parlamentar.objects.get(id=p)
                sessao.save()

            msg = _('Presença em Sessão salva com sucesso!')
            messages.add_message(request, messages.SUCCESS, msg)

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:presenca', kwargs={'pk': pk})


class PainelView(PermissionRequiredForAppCrudMixin, TemplateView):
    template_name = 'sessao/painel.html'
    app_label = 'painel'

    def has_permission(self):
        painel_aberto = AppsAppConfig.attr('painel_aberto')

        if painel_aberto and self.request.user.is_anonymous():
            return True

        return PermissionRequiredForAppCrudMixin.has_permission(self)

    def get(self, request, *args, **kwargs):
        if request.user.is_anonymous():
            self.template_name = 'painel/index.html'
        return TemplateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = TemplateView.get_context_data(self, **kwargs)
        context.update({
            'head_title': str(_('Painel Plenário')),
            'sessao_id': kwargs['pk'],
            'root_pk': kwargs['pk'],
            'sessaoplenaria': SessaoPlenaria.objects.get(pk=kwargs['pk'])})

        return context


class PresencaOrdemDiaView(FormMixin, PresencaMixin, DetailView):
    template_name = 'sessao/presenca_ordemdia.html'
    form_class = PresencaForm
    model = SessaoPlenaria

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Presença Ordem do Dia'), self.object)
        return context

    @method_decorator(permission_required_for_app(AppConfig.label))
    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = self.get_form()

        pk = kwargs['pk']

        if form.is_valid():
            # Pegar os presentes salvos no banco
            presentes_banco = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=pk)

            # Id dos parlamentares presentes
            marcados = request.POST.getlist('presenca')

            # Deletar os que foram desmarcadors
            deletar = set(set(presentes_banco) - set(marcados))
            for d in deletar:
                PresencaOrdemDia.objects.filter(
                    parlamentar_id=d.parlamentar_id).delete()

            for p in marcados:
                ordem = PresencaOrdemDia()
                ordem.sessao_plenaria = self.object
                ordem.parlamentar = Parlamentar.objects.get(id=p)
                ordem.save()

            msg = _('Presença em Ordem do Dia salva com sucesso!')
            messages.add_message(request, messages.SUCCESS, msg)

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:presencaordemdia', kwargs={'pk': pk})


class ListMateriaOrdemDiaView(FormMixin, DetailView):
    template_name = 'sessao/materia_ordemdia_list.html'
    form_class = ListMateriaForm
    model = SessaoPlenaria

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        pk = self.kwargs['pk']
        ordem = OrdemDia.objects.filter(sessao_plenaria_id=pk)

        materias_ordem = []
        for o in ordem:
            ementa = o.observacao
            titulo = o.materia
            numero = o.numero_ordem

            autoria = Autoria.objects.filter(materia_id=o.materia_id)
            autor = [str(a.autor) for a in autoria]

            mat = {'pk': pk,
                   'oid': o.materia_id,
                   'ordem_id': o.id,
                   'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': o.resultado,
                   'autor': autor,
                   'votacao_aberta': o.votacao_aberta,
                   'tipo_votacao': o.tipo_votacao
                   }
            materias_ordem.append(mat)

        sorted(materias_ordem, key=lambda x: x['numero'])

        context.update({'materias_ordem': materias_ordem})

        return self.render_to_response(context)

    @method_decorator(permission_required_for_app(AppConfig.label))
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        pk = self.kwargs['pk']
        form = ListMateriaForm(request.POST)

        # TODO: Existe uma forma de atualizar em lote de acordo
        # com a forma abaixo, mas como setar o primeiro para "1"?
        # OrdemDia.objects.filter(sessao_plenaria_id=pk)
        # .order_by('numero_ordem').update(numero_ordem=3)

        if 'materia_reorder' in request.POST:
            ordens = OrdemDia.objects.filter(sessao_plenaria_id=pk)
            ordem_num = 1
            for o in ordens:
                o.numero_ordem = ordem_num
                o.save()
                ordem_num += 1
        elif 'abrir-votacao' in request.POST:
            existe_votacao_aberta = OrdemDia.objects.filter(
                sessao_plenaria_id=pk, votacao_aberta=True).exists()
            if existe_votacao_aberta:
                context = self.get_context_data(object=self.object)

                form._errors = {'error_message': 'error_message'}
                context.update({'form': form})

                pk = self.kwargs['pk']
                ordem = OrdemDia.objects.filter(sessao_plenaria_id=pk)

                materias_ordem = []
                for o in ordem:
                    ementa = o.observacao
                    titulo = o.materia
                    numero = o.numero_ordem

                    autoria = Autoria.objects.filter(materia_id=o.materia_id)
                    autor = [str(a.autor) for a in autoria]

                    mat = {'pk': pk,
                           'oid': o.materia_id,
                           'ordem_id': o.id,
                           'ementa': ementa,
                           'titulo': titulo,
                           'numero': numero,
                           'resultado': o.resultado,
                           'autor': autor,
                           'votacao_aberta': o.votacao_aberta,
                           'tipo_votacao': o.tipo_votacao
                           }
                    materias_ordem.append(mat)

                sorted(materias_ordem, key=lambda x: x['numero'])
                context.update({'materias_ordem': materias_ordem})
                return self.render_to_response(context)
            else:
                ordem_id = request.POST['ordem_id']
                ordem = OrdemDia.objects.get(id=ordem_id)
                ordem.votacao_aberta = True
                ordem.save()
        return self.get(self, request, args, kwargs)


def ordenar_integrantes_por_cargo(integrantes):
    return sorted(integrantes, key=lambda k: k['cargo'].id)


class MesaView(FormMixin, DetailView):
    template_name = 'sessao/mesa.html'
    form_class = MesaForm
    model = SessaoPlenaria

    def get(self, request, *args, **kwargs):

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        mesa = IntegranteMesa.objects.filter(
            sessao_plenaria=self.object)

        integrantes = []
        for m in mesa:
            parlamentar = Parlamentar.objects.get(
                id=m.parlamentar_id)
            cargo = CargoMesa.objects.get(
                id=m.cargo_id)
            integrante = {'parlamentar': parlamentar, 'cargo': cargo}
            integrantes.append(integrante)

        context.update(
            {'integrantes': ordenar_integrantes_por_cargo(integrantes)})

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Mesa Diretora'), self.object)
        return context

    @method_decorator(permission_required_for_app(AppConfig.label))
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = MesaForm(request.POST)

        if 'Incluir' in request.POST:
            if form.is_valid():
                integrante = IntegranteMesa()
                integrante.sessao_plenaria_id = self.object.id
                integrante.parlamentar_id = request.POST['parlamentar']
                integrante.cargo_id = request.POST['cargo']
                integrante.save()

                return self.form_valid(form)

            else:
                form.clean()
                return self.form_valid(form)
        elif 'Excluir' in request.POST:
            if 'composicao_mesa' in request.POST:
                ids = request.POST['composicao_mesa'].split(':')
                IntegranteMesa.objects.get(
                    sessao_plenaria_id=self.object.id,
                    parlamentar_id=ids[0],
                    cargo_id=ids[1]
                ).delete()
            else:
                pass
                # TODO display message asking to select a member of list

        return self.form_valid(form)

    def get_candidatos_mesa(self):
        self.object = self.get_object()
        lista_parlamentares = []
        lista_integrantes = []

        for parlamentar in Parlamentar.objects.all():
            if parlamentar.ativo:
                lista_parlamentares.append(parlamentar)

        for integrante in IntegranteMesa.objects.filter(
                sessao_plenaria=self.object):
            parlamentar = Parlamentar.objects.get(
                id=integrante.parlamentar_id)
            lista_integrantes.append(parlamentar)

        lista = list(set(lista_parlamentares) - set(lista_integrantes))
        lista.sort(key=lambda x: x.nome_parlamentar)
        return lista

    def get_cargos_mesa(self):
        self.object = self.get_object()
        lista_cargos = CargoMesa.objects.all()
        lista_cargos_ocupados = []

        for integrante in IntegranteMesa.objects.filter(
                sessao_plenaria=self.object):
            cargo = CargoMesa.objects.get(
                id=integrante.cargo_id)
            lista_cargos_ocupados.append(cargo)

        lista = list(set(lista_cargos) - set(lista_cargos_ocupados))
        return lista

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:mesa', kwargs={'pk': pk})


class ResumoView(DetailView):
    template_name = 'sessao/resumo.html'
    model = SessaoPlenaria

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # =====================================================================
        # Identificação Básica
        data_inicio = self.object.data_inicio
        abertura = data_inicio.strftime('%d/%m/%Y') if data_inicio else ''

        data_fim = self.object.data_fim
        encerramento = data_fim.strftime('%d/%m/%Y') if data_fim else ''

        context.update({'basica': [
            _('Tipo de Sessão: %(tipo)s') % {'tipo': self.object.tipo},
            _('Abertura: %(abertura)s - %(hora_inicio)s') % {
                'abertura': abertura, 'hora_inicio': self.object.hora_inicio},
            _('Encerramento: %(encerramento)s - %(hora_fim)s') % {
                'encerramento': encerramento, 'hora_fim': self.object.hora_fim}
        ]})
        # =====================================================================
        # Conteúdo Multimídia
        if self.object.url_audio:
            context.update({'multimidia_audio':
                            _('Audio: ') + str(self.object.url_audio)})
        else:
            context.update({'multimidia_audio': _('Audio: Indisponivel')})

        if self.object.url_video:
            context.update({'multimidia_video':
                            _('Video: ') + str(self.object.url_video)})
        else:
            context.update({'multimidia_video': _('Video: Indisponivel')})

        # =====================================================================
        # Mesa Diretora
        mesa = IntegranteMesa.objects.filter(
            sessao_plenaria=self.object)

        integrantes = []
        for m in mesa:
            parlamentar = Parlamentar.objects.get(
                id=m.parlamentar_id)
            cargo = CargoMesa.objects.get(
                id=m.cargo_id)
            integrante = {'parlamentar': parlamentar, 'cargo': cargo}
            integrantes.append(integrante)

        context.update({'mesa': ordenar_integrantes_por_cargo(integrantes)})

        # =====================================================================
        # Presença Sessão
        presencas = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id
        )

        parlamentares_sessao = []
        for p in presencas:
            parlamentar = Parlamentar.objects.get(
                id=p.parlamentar_id)
            parlamentares_sessao.append(parlamentar)

        context.update({'presenca_sessao': parlamentares_sessao})

        # =====================================================================
        # Expedientes
        expediente = ExpedienteSessao.objects.filter(
            sessao_plenaria_id=self.object.id).order_by('tipo__nome')

        expedientes = []
        for e in expediente:
            tipo = TipoExpediente.objects.get(id=e.tipo_id)
            conteudo = e.conteudo
            ex = {'tipo': tipo, 'conteudo': conteudo}
            expedientes.append(ex)
        context.update({'expedientes': expedientes})

        # =====================================================================
        # Matérias Expediente
        materias = ExpedienteMateria.objects.filter(
            sessao_plenaria_id=self.object.id)

        materias_expediente = []
        for m in materias:
            ementa = m.observacao
            titulo = m.materia
            numero = m.numero_ordem

            if m.resultado:
                resultado = m.resultado
            else:
                resultado = _('Matéria não votada')

            autoria = Autoria.objects.filter(materia_id=m.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'autor': autor
                   }
            materias_expediente.append(mat)

        context.update({'materia_expediente': materias_expediente})

        # =====================================================================
        # Oradores Expediente
        oradores = []
        for orador in OradorExpediente.objects.filter(
                sessao_plenaria_id=self.object.id):
            numero_ordem = orador.numero_ordem
            url_discurso = orador.url_discurso
            parlamentar = Parlamentar.objects.get(
                id=orador.parlamentar_id)
            ora = {'numero_ordem': numero_ordem,
                   'url_discurso': url_discurso,
                   'parlamentar': parlamentar
                   }
            oradores.append(ora)

        context.update({'oradores': oradores})

        # =====================================================================
        # Presença Ordem do Dia
        presencas = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id
        )

        parlamentares_ordem = []
        for p in presencas:
            parlamentar = Parlamentar.objects.get(
                id=p.parlamentar_id)
            parlamentares_ordem.append(parlamentar)

        context.update({'presenca_ordem': parlamentares_ordem})

        # =====================================================================
        # Matérias Ordem do Dia
        ordem = OrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id)

        materias_ordem = []
        for o in ordem:
            ementa = o.observacao
            titulo = o.materia
            numero = o.numero_ordem

            # Verificar resultado
            if o.resultado:
                resultado = o.resultado
            else:
                resultado = _('Matéria não votada')

            autoria = Autoria.objects.filter(
                materia_id=o.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'autor': autor
                   }
            materias_ordem.append(mat)

        context.update({'materias_ordem': materias_ordem})

        return self.render_to_response(context)


class ExpedienteView(FormMixin, DetailView):
    template_name = 'sessao/expediente.html'
    form_class = ExpedienteForm
    model = SessaoPlenaria

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Expediente Diversos'), self.object)
        return context

    @method_decorator(permission_required_for_app(AppConfig.label))
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ExpedienteForm(request.POST)

        if form.is_valid():
            list_tipo = request.POST.getlist('tipo')
            list_conteudo = request.POST.getlist('conteudo')

            for tipo, conteudo in zip(list_tipo, list_conteudo):
                try:
                    ExpedienteSessao.objects.get(
                        sessao_plenaria_id=self.object.id,
                        tipo_id=tipo
                    ).delete()
                except:
                    pass

                expediente = ExpedienteSessao()
                expediente.sessao_plenaria_id = self.object.id
                expediente.tipo_id = tipo
                expediente.conteudo = conteudo
                expediente.save()
            return self.form_valid(form)
        else:
            return self.form_valid(form)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        tipos = TipoExpediente.objects.all().order_by('nome')
        expedientes_sessao = ExpedienteSessao.objects.filter(
            sessao_plenaria_id=self.object.id).order_by('tipo__nome')

        expedientes_salvos = []
        for e in expedientes_sessao:
            expedientes_salvos.append(e.tipo)

        tipos_null = list(set(tipos) - set(expedientes_salvos))
        tipos_null.sort(key=lambda x: x.nome)

        expedientes = []
        for e, t in zip(expedientes_sessao, tipos):
            expedientes.append({'tipo': e.tipo,
                                'conteudo': e.conteudo
                                })
        context.update({'expedientes': expedientes})

        for e in tipos_null:
            expedientes.append({'tipo': e,
                                'conteudo': ''
                                })

        context.update({'expedientes': expedientes})
        return self.render_to_response(context)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:expediente', kwargs={'pk': pk})


class VotacaoEditView(SessaoPermissionMixin):

    '''
        Votação Simbólica e Secreta
    '''

    template_name = 'sessao/votacao/votacao_edit.html'

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = VotacaoEditForm(request.POST)

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        if(int(request.POST['anular_votacao']) == 1):
            RegistroVotacao.objects.filter(
                materia_id=materia_id,
                ordem_id=ordem_id).last().delete()

            ordem = OrdemDia.objects.get(
                sessao_plenaria_id=self.object.id,
                materia_id=materia_id)
            ordem.votacao_aberta = False
            ordem.resultado = ''
            ordem.save()

        return self.form_valid(form)

    def get(self, request, *args, **kwargs):
        context = {}

        url = request.get_full_path()

        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        ordem = OrdemDia.objects.get(id=ordem_id)

        materia = {'materia': ordem.materia, 'ementa': ordem.observacao}
        context.update({'materia': materia})

        votacao = RegistroVotacao.objects.filter(
            materia_id=materia_id,
            ordem_id=ordem_id).last()
        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao_titulo': titulo,
                        'votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:ordemdia_list',
                       kwargs={'pk': pk})


class VotacaoView(SessaoPermissionMixin):

    '''
        Votação Simbólica e Secreta
    '''

    template_name = 'sessao/votacao/votacao.html'
    form_class = VotacaoForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # TODO: HACK, VERIFICAR MELHOR FORMA DE FAZER ISSO
        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        ordem_id = kwargs['mid']
        ordem = OrdemDia.objects.get(id=ordem_id)
        qtde_presentes = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': ordem.materia, 'ementa': ordem.observacao}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoForm(request.POST)
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # ====================================================
        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        ordem_id = kwargs['mid']
        ordem = OrdemDia.objects.get(id=ordem_id)
        qtde_presentes = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': ordem.materia, 'ementa': ordem.observacao}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes})
        context.update({'form': form})
        # ====================================================

        if 'cancelar-votacao' in request.POST:
            ordem.votacao_aberta = False
            ordem.save()
            return self.form_valid(form)

        if form.is_valid():
            materia_id = kwargs['oid']
            ordem_id = kwargs['mid']

            qtde_presentes = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=self.object.id).count()
            qtde_votos = (int(request.POST['votos_sim']) +
                          int(request.POST['votos_nao']) +
                          int(request.POST['abstencoes']))

            if (int(request.POST['voto_presidente']) == 0):
                qtde_presentes -= 1

            if (qtde_votos > qtde_presentes or qtde_votos < qtde_presentes):
                form._errors["total_votos"] = ErrorList([u""])
                return self.render_to_response(context)
            elif (qtde_presentes == qtde_votos):
                try:
                    votacao = RegistroVotacao()
                    votacao.numero_votos_sim = int(request.POST['votos_sim'])
                    votacao.numero_votos_nao = int(request.POST['votos_nao'])
                    votacao.numero_abstencoes = int(request.POST['abstencoes'])
                    votacao.observacao = request.POST['observacao']
                    votacao.materia_id = materia_id
                    votacao.ordem_id = ordem_id
                    votacao.tipo_resultado_votacao_id = int(
                        request.POST['resultado_votacao'])
                    votacao.save()
                except:
                    return self.form_invalid(form)
                else:
                    ordem = OrdemDia.objects.get(
                        sessao_plenaria_id=self.object.id,
                        materia_id=materia_id)
                    resultado = TipoResultadoVotacao.objects.get(
                        id=request.POST['resultado_votacao'])
                    ordem.resultado = resultado.nome
                    ordem.votacao_aberta = False
                    ordem.save()

                return self.form_valid(form)
        else:
            return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:ordemdia_list',
                       kwargs={'pk': pk})


class VotacaoNominalView(SessaoPermissionMixin):
    template_name = 'sessao/votacao/nominal.html'

    def get(self, request, *args, **kwargs):
        ordem_id = kwargs['mid']
        ordem = OrdemDia.objects.get(id=ordem_id)

        materia = {'materia': ordem.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(ordem.observacao))}
        context = {'materia': materia, 'object': self.get_object(),
                   'parlamentares': self.get_parlamentares(),
                   'tipos': self.get_tipos_votacao()}

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        ordem_id = kwargs['mid']
        ordem = OrdemDia.objects.get(id=ordem_id)

        form = VotacaoNominalForm(request.POST)

        if 'cancelar-votacao' in request.POST:
            ordem.votacao_aberta = False
            ordem.save()
            return self.form_valid(form)

        if form.is_valid():
            materia_id = kwargs['oid']
            ordem_id = kwargs['mid']

            votos_sim = 0
            votos_nao = 0
            abstencoes = 0
            nao_votou = 0

            for votos in request.POST.getlist('voto_parlamentar'):
                v = votos.split(':')
                voto = v[0]
                parlamentar_id = v[1]

                if(voto == 'sim'):
                    votos_sim += 1
                elif(voto == 'nao'):
                    votos_nao += 1
                elif(voto == 'abstencao'):
                    abstencoes += 1
                elif(voto == 'nao_votou'):
                    nao_votou += 1

            try:
                votacao = RegistroVotacao.objects.get(
                    materia_id=materia_id,
                    ordem_id=ordem_id)
            except ObjectDoesNotExist:
                pass
            else:
                votacao.delete()

            votacao = RegistroVotacao()
            votacao.numero_votos_sim = votos_sim
            votacao.numero_votos_nao = votos_nao
            votacao.numero_abstencoes = abstencoes
            votacao.observacao = request.POST['observacao']
            votacao.materia_id = materia_id
            votacao.ordem_id = ordem_id
            votacao.tipo_resultado_votacao_id = int(
                request.POST['resultado_votacao'])
            votacao.save()

            for votos in request.POST.getlist('voto_parlamentar'):
                v = votos.split(':')
                voto = v[0]
                parlamentar_id = v[1]

                voto_parlamentar = VotoParlamentar()
                if voto == 'sim':
                    voto_parlamentar.voto = _('Sim')
                elif voto == 'nao':
                    voto_parlamentar.voto = _('Não')
                elif voto == 'abstencao':
                    voto_parlamentar.voto = _('Abstenção')
                elif voto == 'nao_votou':
                    voto_parlamentar.voto = _('Não Votou')
                voto_parlamentar.parlamentar_id = parlamentar_id
                voto_parlamentar.votacao_id = votacao.id
                voto_parlamentar.save()

                ordem = OrdemDia.objects.get(
                    sessao_plenaria_id=self.object.id,
                    materia_id=materia_id)
                resultado = TipoResultadoVotacao.objects.get(
                    id=request.POST['resultado_votacao'])
                ordem.resultado = resultado.nome
                ordem.votacao_aberta = False
                ordem.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_parlamentares(self):
        self.object = self.get_object()

        presencas = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id
        )
        presentes = [p.parlamentar for p in presencas]

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                yield parlamentar

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:ordemdia_list',
                       kwargs={'pk': pk})


class VotacaoNominalEditView(SessaoPermissionMixin):
    template_name = 'sessao/votacao/nominal_edit.html'

    def get(self, request, *args, **kwargs):
        context = {}

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        votacao = RegistroVotacao.objects.get(
            materia_id=materia_id,
            ordem_id=ordem_id)
        ordem = OrdemDia.objects.get(id=ordem_id)
        votos = VotoParlamentar.objects.filter(votacao_id=votacao.id)

        list_votos = []
        for v in votos:
            parlamentar = Parlamentar.objects.get(id=v.parlamentar_id)
            list_votos.append({'parlamentar': parlamentar, 'voto': v.voto})

        context.update({'votos': list_votos})

        materia = {'materia': ordem.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(ordem.observacao))}
        context.update({'materia': materia})

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoEditForm(request.POST)

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        if(int(request.POST['anular_votacao']) == 1):
            registro = RegistroVotacao.objects.get(
                materia_id=materia_id,
                ordem_id=ordem_id)

            ordem = OrdemDia.objects.get(
                sessao_plenaria_id=self.object.id,
                materia_id=materia_id)
            ordem.resultado = ''
            ordem.votacao_aberta = False
            ordem.save()

            try:
                votacao = VotoParlamentar.objects.filter(
                    votacao_id=registro.id)
                for v in votacao:
                    v.delete()
            except:
                pass

            registro.delete()

        return self.form_valid(form)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:ordemdia_list',
                       kwargs={'pk': pk})


class VotacaoNominalExpedienteView(SessaoPermissionMixin):
    template_name = 'sessao/votacao/nominal.html'

    def get(self, request, *args, **kwargs):
        expediente_id = kwargs['mid']
        expediente = ExpedienteMateria.objects.get(id=expediente_id)

        materia = {'materia': expediente.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(expediente.observacao))}
        context = {'materia': materia, 'object': self.get_object(),
                   'parlamentares': self.get_parlamentares(),
                   'tipos': self.get_tipos_votacao()}

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        expediente_id = kwargs['mid']
        expediente = ExpedienteMateria.objects.get(id=expediente_id)

        form = VotacaoNominalForm(request.POST)

        if 'cancelar-votacao' in request.POST:
            expediente.votacao_aberta = False
            expediente.save()
            return self.form_valid(form)

        if form.is_valid():
            materia_id = kwargs['oid']
            expediente_id = kwargs['mid']

            votos_sim = 0
            votos_nao = 0
            abstencoes = 0
            nao_votou = 0

            for votos in request.POST.getlist('voto_parlamentar'):
                v = votos.split(':')
                voto = v[0]
                parlamentar_id = v[1]

                if(voto == 'sim'):
                    votos_sim += 1
                elif(voto == 'nao'):
                    votos_nao += 1
                elif(voto == 'abstencao'):
                    abstencoes += 1
                elif(voto == 'nao_votou'):
                    nao_votou += 1

            try:
                votacao = RegistroVotacao()
                votacao.numero_votos_sim = votos_sim
                votacao.numero_votos_nao = votos_nao
                votacao.numero_abstencoes = abstencoes
                votacao.observacao = request.POST['observacao']
                votacao.materia_id = materia_id
                votacao.expediente = expediente
                votacao.tipo_resultado_votacao_id = int(
                    request.POST['resultado_votacao'])
                votacao.save()
            except:
                return self.form_invalid(form)
            else:
                votacao = RegistroVotacao.objects.get(
                    materia_id=materia_id,
                    expediente_id=expediente)

                for votos in request.POST.getlist('voto_parlamentar'):
                    v = votos.split(':')
                    voto = v[0]
                    parlamentar_id = v[1]

                    voto_parlamentar = VotoParlamentar()
                    if(voto == 'sim'):
                        voto_parlamentar.voto = _('Sim')
                    elif(voto == 'nao'):
                        voto_parlamentar.voto = _('Não')
                    elif(voto == 'abstencao'):
                        voto_parlamentar.voto = _('Abstenção')
                    elif(voto == 'nao_votou'):
                        voto_parlamentar.voto = _('Não Votou')
                    voto_parlamentar.parlamentar_id = parlamentar_id
                    voto_parlamentar.votacao_id = votacao.id
                    voto_parlamentar.save()

                    expediente = ExpedienteMateria.objects.get(
                        sessao_plenaria_id=self.object.id,
                        materia_id=materia_id)
                    resultado = TipoResultadoVotacao.objects.get(
                        id=request.POST['resultado_votacao'])
                    expediente.resultado = resultado.nome
                    expediente.votacao_aberta = False
                    expediente.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_parlamentares(self):
        self.object = self.get_object()

        presencas = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id
        )
        presentes = [p.parlamentar for p in presencas]

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                yield parlamentar

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:expedientemateria_list',
                       kwargs={'pk': pk})


class VotacaoNominalExpedienteEditView(SessaoPermissionMixin):
    template_name = 'sessao/votacao/nominal_edit.html'

    def get(self, request, *args, **kwargs):
        context = {}
        materia_id = kwargs['oid']
        expediente_id = kwargs['mid']

        votacao = RegistroVotacao.objects.get(
            materia_id=materia_id,
            expediente_id=expediente_id)
        expediente = ExpedienteMateria.objects.get(id=expediente_id)
        votos = VotoParlamentar.objects.filter(votacao_id=votacao.id)

        list_votos = []
        for v in votos:
            parlamentar = Parlamentar.objects.get(id=v.parlamentar_id)
            list_votos.append({'parlamentar': parlamentar, 'voto': v.voto})

        context.update({'votos': list_votos})

        materia = {'materia': expediente.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(expediente.observacao))}
        context.update({'materia': materia})

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoEditForm(request.POST)

        materia_id = kwargs['oid']
        expediente_id = kwargs['mid']

        if(int(request.POST['anular_votacao']) == 1):
            registro = RegistroVotacao.objects.get(
                materia_id=materia_id,
                expediente_id=expediente_id)

            expediente = ExpedienteMateria.objects.get(
                sessao_plenaria_id=self.object.id,
                materia_id=materia_id)
            expediente.resultado = ''
            expediente.votacao_aberta = False
            expediente.save()

            try:
                votacao = VotoParlamentar.objects.filter(
                    votacao_id=registro.id)
                for v in votacao:
                    v.delete()
            except:
                pass

            registro.delete()

        return self.form_valid(form)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:expedientemateria_list',
                       kwargs={'pk': pk})


class VotacaoExpedienteView(SessaoPermissionMixin):

    '''
        Votação Simbólica e Secreta
    '''

    template_name = 'sessao/votacao/votacao.html'
    form_class = VotacaoForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # TODO: HACK, VERIFICAR MELHOR FORMA DE FAZER ISSO
        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        expediente_id = kwargs['mid']
        expediente = ExpedienteMateria.objects.get(id=expediente_id)
        qtde_presentes = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': expediente.materia,
                   'ementa': expediente.observacao}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoForm(request.POST)
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # ====================================================
        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        expediente_id = kwargs['mid']
        expediente = ExpedienteMateria.objects.get(id=expediente_id)
        qtde_presentes = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': expediente.materia,
                   'ementa': expediente.observacao}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes})
        context.update({'form': form})
        # ====================================================

        if 'cancelar-votacao' in request.POST:
            expediente.votacao_aberta = False
            expediente.save()
            return self.form_valid(form)

        if form.is_valid():
            materia_id = kwargs['oid']
            expediente_id = kwargs['mid']

            qtde_presentes = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=self.object.id).count()
            qtde_votos = (int(request.POST['votos_sim']) +
                          int(request.POST['votos_nao']) +
                          int(request.POST['abstencoes']))

            if (int(request.POST['voto_presidente']) == 0):
                qtde_presentes -= 1

            if (qtde_votos > qtde_presentes or qtde_votos < qtde_presentes):
                form._errors["total_votos"] = ErrorList([u""])
                return self.render_to_response(context)
            elif (qtde_presentes == qtde_votos):
                try:
                    votacao = RegistroVotacao()
                    votacao.numero_votos_sim = int(request.POST['votos_sim'])
                    votacao.numero_votos_nao = int(request.POST['votos_nao'])
                    votacao.numero_abstencoes = int(request.POST['abstencoes'])
                    votacao.observacao = request.POST['observacao']
                    votacao.materia_id = materia_id
                    votacao.expediente_id = expediente_id
                    votacao.tipo_resultado_votacao_id = int(
                        request.POST['resultado_votacao'])
                    votacao.save()
                except:
                    return self.form_invalid(form)
                else:
                    expediente = ExpedienteMateria.objects.get(
                        sessao_plenaria_id=self.object.id,
                        materia_id=materia_id)
                    resultado = TipoResultadoVotacao.objects.get(
                        id=request.POST['resultado_votacao'])
                    expediente.resultado = resultado.nome
                    expediente.votacao_aberta = False
                    expediente.save()

                return self.form_valid(form)
        else:
            return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:expedientemateria_list',
                       kwargs={'pk': pk})


class VotacaoExpedienteEditView(SessaoPermissionMixin):

    '''
        Votação Simbólica e Secreta
    '''

    template_name = 'sessao/votacao/votacao_edit.html'
    form_class = VotacaoEditForm

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:expedientemateria_list',
                       kwargs={'pk': pk})

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        url = request.get_full_path()

        if "votsimb" in url:
            titulo = _("Votação Simbólica")
        elif "votsec" in url:
            titulo = _("Votação Secreta")
        else:
            titulo = _("Não definida")

        materia_id = kwargs['oid']
        expediente_id = kwargs['mid']

        expediente = ExpedienteMateria.objects.get(id=expediente_id)

        materia = {'materia': expediente.materia,
                   'ementa': expediente.observacao}
        context.update({'materia': materia})

        votacao = RegistroVotacao.objects.get(
            materia_id=materia_id,
            expediente_id=expediente_id)
        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao_titulo': titulo,
                        'votacao': votacao_existente})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = VotacaoEditForm(request.POST)

        materia_id = kwargs['oid']
        expediente_id = kwargs['mid']

        if(int(request.POST['anular_votacao']) == 1):
            RegistroVotacao.objects.get(
                materia_id=materia_id,
                expediente_id=expediente_id).delete()

            expediente = ExpedienteMateria.objects.get(
                sessao_plenaria_id=self.object.id,
                materia_id=materia_id)
            expediente.votacao_aberta = False
            expediente.resultado = ''
            expediente.save()

        return self.form_valid(form)


class SessaoListView(ListView):
    template_name = "sessao/sessao_list.html"
    paginate_by = 10
    model = SessaoPlenaria

    def get_queryset(self):
        return SessaoPlenaria.objects.all().order_by('-data_inicio')

    def get_context_data(self, **kwargs):
        context = super(SessaoListView, self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        return context


class PautaSessaoListView(SessaoListView):
    template_name = "sessao/pauta_sessao_list.html"


class PautaSessaoDetailView(DetailView):
    template_name = "sessao/pauta_sessao_detail.html"
    model = SessaoPlenaria

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # =====================================================================
        # Identificação Básica
        abertura = self.object.data_inicio.strftime('%d/%m/%Y')
        if self.object.data_fim:
            encerramento = self.object.data_fim.strftime('%d/%m/%Y')
        else:
            encerramento = ""

        context.update({'basica': [
            _('Tipo de Sessão: %(tipo)s') % {'tipo': self.object.tipo},
            _('Abertura: %(abertura)s') % {'abertura': abertura},
            _('Encerramento: %(encerramento)s') % {
                'encerramento': encerramento},
        ]})
        # =====================================================================
        # Matérias Expediente
        materias = ExpedienteMateria.objects.filter(
            sessao_plenaria_id=self.object.id)

        materias_expediente = []
        for m in materias:
            ementa = m.observacao
            titulo = m.materia
            numero = m.numero_ordem

            if m.resultado:
                resultado = m.resultado
            else:
                resultado = _('Matéria não votada')

            autoria = Autoria.objects.filter(materia_id=m.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'id': m.id,
                   'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'autor': autor
                   }
            materias_expediente.append(mat)

        context.update({'materia_expediente': materias_expediente})
        # =====================================================================
        # Expedientes
        expediente = ExpedienteSessao.objects.filter(
            sessao_plenaria_id=self.object.id)

        expedientes = []
        for e in expediente:
            tipo = TipoExpediente.objects.get(
                id=e.tipo_id)
            conteudo = sub(
                '&nbsp;', ' ', strip_tags(e.conteudo))

            ex = {'tipo': tipo, 'conteudo': conteudo}
            expedientes.append(ex)

        context.update({'expedientes': expedientes})
        # =====================================================================
        # Orador Expediente
        oradores = OradorExpediente.objects.filter(
            sessao_plenaria_id=self.object.id).order_by('numero_ordem')
        context.update({'oradores': oradores})
        # =====================================================================
        # Matérias Ordem do Dia
        ordem = OrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id)

        materias_ordem = []
        for o in ordem:
            ementa = o.observacao
            titulo = o.materia
            numero = o.numero_ordem

            # Verificar resultado
            if o.resultado:
                resultado = o.resultado
            else:
                resultado = _('Matéria não votada')

            autoria = Autoria.objects.filter(
                materia_id=o.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'id': o.id,
                   'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'autor': autor
                   }
            materias_ordem.append(mat)

        context.update({'materias_ordem': materias_ordem})

        return self.render_to_response(context)


class SessaoPlenariaView(generics.ListAPIView):
    queryset = SessaoPlenaria.objects.all()
    serializer_class = SessaoPlenariaSerializer


class PautaExpedienteDetail(DetailView):
    template_name = "sessao/pauta/expediente.html"
    model = SessaoPlenaria

    def get(self, request, *args, **kwargs):
        pk = self.kwargs['pk']

        expediente = ExpedienteMateria.objects.get(id=pk)
        doc_ace = DocumentoAcessorio.objects.filter(
            materia=expediente.materia)
        tramitacao = Tramitacao.objects.filter(
            materia=expediente.materia)

        return self.render_to_response(
            {'expediente': expediente,
             'doc_ace': doc_ace,
             'tramitacao': tramitacao})


class PautaOrdemDetail(DetailView):
    template_name = "sessao/pauta/ordem.html"
    model = SessaoPlenaria

    def get(self, request, *args, **kwargs):
        pk = self.kwargs['pk']

        ordem = OrdemDia.objects.get(id=pk)
        norma = NormaJuridica.objects.filter(
            materia=ordem.materia)
        doc_ace = DocumentoAcessorio.objects.filter(
            materia=ordem.materia)
        tramitacao = Tramitacao.objects.filter(
            materia=ordem.materia)

        return self.render_to_response(
            {'ordem': ordem,
             'norma': norma,
             'doc_ace': doc_ace,
             'tramitacao': tramitacao})


class PesquisarSessaoPlenariaView(FilterView):
    model = SessaoPlenaria
    filterset_class = SessaoPlenariaFilterSet
    paginate_by = 10

    def get_filterset_kwargs(self, filterset_class):
        super(PesquisarSessaoPlenariaView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset()

        qs = qs.distinct().order_by(
            '-legislatura__numero', '-data_inicio', '-numero')

        kwargs.update({
            'queryset': qs,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(PesquisarSessaoPlenariaView,
                        self).get_context_data(**kwargs)

        context['title'] = _('Pesquisar Sessão Plenária')
        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        return context

    def get(self, request, *args, **kwargs):
        super(PesquisarSessaoPlenariaView, self).get(request)

        # Se a pesquisa estiver quebrando com a paginação
        # Olhe esta função abaixo
        # Provavelmente você criou um novo campo no Form/FilterSet
        # Então a ordem da URL está diferente
        data = self.filterset.data
        if (data and data.get('data_inicio__year') is not None):
            url = "&" + str(self.request.environ['QUERY_STRING'])
            if url.startswith("&page"):
                ponto_comeco = url.find('data_inicio__year=') - 1
                url = url[ponto_comeco:]
        else:
            url = ''

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list,
                                        filter_url=url,
                                        numero_res=len(self.object_list)
                                        )

        return self.render_to_response(context)


class PesquisarPautaSessaoView(PesquisarSessaoPlenariaView):
    filterset_class = PautaSessaoFilterSet
    template_name = 'sessao/pauta_sessao_filter.html'


def filtra_tramitacao_ordem_dia():
    lista = pega_ultima_tramitacao()
    return Tramitacao.objects.filter(
        id__in=lista,
        status__descricao='Ordem do Dia').distinct().values_list(
        'materia_id', flat=True)


def retira_materias_ja_adicionadas(id_sessao, model):
    lista = model.objects.filter(
        sessao_plenaria_id=id_sessao)
    lista_id_materias = [l.materia_id for l in lista]
    return lista_id_materias


class AdicionarVariasMateriasExpediente(PermissionRequiredForAppCrudMixin,
                                        MateriaLegislativaPesquisaView):
    filterset_class = AdicionarVariasMateriasFilterSet
    template_name = 'sessao/adicionar_varias_materias_expediente.html'
    app_label = AppConfig.label

    def get_filterset_kwargs(self, filterset_class):
        super(AdicionarVariasMateriasExpediente,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset()

        lista_ordem_dia = filtra_tramitacao_ordem_dia()

        lista_materias_adicionadas = retira_materias_ja_adicionadas(
            self.kwargs['pk'], ExpedienteMateria)

        qs = qs.filter(id__in=lista_ordem_dia).exclude(
            id__in=lista_materias_adicionadas).distinct()

        kwargs.update({
            'queryset': qs,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(MateriaLegislativaPesquisaView,
                        self).get_context_data(**kwargs)

        context['title'] = _('Pesquisar Matéria Legislativa')

        self.filterset.form.fields['o'].label = _('Ordenação')

        qr = self.request.GET.copy()

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''
        context['pk_sessao'] = self.kwargs['pk']

        return context

    def post(self, request, *args, **kwargs):
        marcadas = request.POST.getlist('materia_id')

        for m in marcadas:
            try:
                tipo_votacao = request.POST['tipo_votacao_%s' % m]
            except MultiValueDictKeyError:
                msg = _('Formulário Inválido. Você esqueceu de selecionar ' +
                        'o tipo de votação de %s' %
                        MateriaLegislativa.objects.get(id=m))
                messages.add_message(request, messages.ERROR, msg)
                return self.get(request, self.kwargs)

            if tipo_votacao:
                lista_materias_expediente = ExpedienteMateria.objects.filter(
                    sessao_plenaria_id=self.kwargs[
                        'pk'])

                materia = MateriaLegislativa.objects.get(id=m)

                expediente = ExpedienteMateria()
                expediente.sessao_plenaria_id = self.kwargs['pk']
                expediente.materia_id = materia.id
                expediente.observacao = MateriaLegislativa.objects.get(
                    pk=materia.id).ementa
                if lista_materias_expediente:
                    posicao = lista_materias_expediente.last().numero_ordem + 1
                    expediente.numero_ordem = posicao
                else:
                    expediente.numero_ordem = 1
                expediente.data_ordem = datetime.now()
                expediente.tipo_votacao = request.POST['tipo_votacao_%s' % m]
                expediente.save()

        pk = self.kwargs['pk']

        return HttpResponseRedirect(
            reverse('sapl.sessao:expedientemateria_list', kwargs={'pk': pk}))


class AdicionarVariasMateriasOrdemDia(AdicionarVariasMateriasExpediente):
    filterset_class = AdicionarVariasMateriasFilterSet
    template_name = 'sessao/adicionar_varias_materias_ordem.html'

    def get_filterset_kwargs(self, filterset_class):
        super(AdicionarVariasMateriasExpediente,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset()

        lista_ordem_dia = filtra_tramitacao_ordem_dia()

        lista_materias_adicionadas = retira_materias_ja_adicionadas(
            self.kwargs['pk'], OrdemDia)

        qs = qs.filter(id__in=lista_ordem_dia).exclude(
            id__in=lista_materias_adicionadas).distinct()

        kwargs.update({
            'queryset': qs,
        })
        return kwargs

    def post(self, request, *args, **kwargs):
        marcadas = request.POST.getlist('materia_id')

        for m in marcadas:
            try:
                tipo_votacao = request.POST['tipo_votacao_%s' % m]
            except MultiValueDictKeyError:
                msg = _('Formulário Inválido. Você esqueceu de selecionar ' +
                        'o tipo de votação de %s' %
                        MateriaLegislativa.objects.get(id=m))
                messages.add_message(request, messages.ERROR, msg)
                return self.get(request, self.kwargs)

            if tipo_votacao:
                lista_materias_ordem_dia = OrdemDia.objects.filter(
                    sessao_plenaria_id=self.kwargs[
                        'pk'])

                materia = MateriaLegislativa.objects.get(id=m)

                ordem_dia = OrdemDia()
                ordem_dia.sessao_plenaria_id = self.kwargs['pk']
                ordem_dia.materia_id = materia.id
                ordem_dia.observacao = MateriaLegislativa.objects.get(
                    pk=materia.id).ementa
                if lista_materias_ordem_dia:
                    posicao = lista_materias_ordem_dia.last().numero_ordem + 1
                    ordem_dia.numero_ordem = posicao
                else:
                    ordem_dia.numero_ordem = 1
                ordem_dia.data_ordem = datetime.now()
                ordem_dia.tipo_votacao = tipo_votacao
                ordem_dia.save()

        return self.get(request, self.kwargs)
