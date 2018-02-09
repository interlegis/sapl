from re import sub

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Max, Q
from django.forms.utils import ErrorList
from django.http import JsonResponse
from django.http.response import Http404, HttpResponseRedirect
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, ListView, TemplateView
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django_filters.views import FilterView
from sapl.base.models import AppConfig as AppsAppConfig
from sapl.crud.base import (RP_DETAIL, RP_LIST, Crud, CrudAux,
                            MasterDetailCrud,
                            PermissionRequiredForAppCrudMixin, make_pagination)
from sapl.materia.forms import filtra_tramitacao_status
from sapl.materia.models import (Autoria, DocumentoAcessorio,
                                 TipoMateriaLegislativa, Tramitacao)
from sapl.materia.views import MateriaLegislativaPesquisaView
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import (Filiacao, Legislatura, Mandato,
                                       Parlamentar, SessaoLegislativa)
from sapl.sessao.apps import AppConfig
from sapl.sessao.forms import ExpedienteMateriaForm, OrdemDiaForm
from sapl.utils import show_results_filter_set

from .forms import (AdicionarVariasMateriasFilterSet, BancadaForm, BlocoForm,
                    ExpedienteForm, ListMateriaForm, MesaForm,
                    OradorExpedienteForm, OradorForm, PautaSessaoFilterSet,
                    PresencaForm, ResumoOrdenacaoForm, SessaoPlenariaFilterSet,
                    SessaoPlenariaForm, VotacaoEditForm, VotacaoForm,
                    VotacaoNominalForm)
from .models import (Bancada, Bloco, CargoBancada, CargoMesa,
                     ExpedienteMateria, ExpedienteSessao, IntegranteMesa,
                     MateriaLegislativa, Orador, OradorExpediente, OrdemDia,
                     PresencaOrdemDia, RegistroVotacao, ResumoOrdenacao,
                     SessaoPlenaria, SessaoPlenariaPresenca, TipoExpediente,
                     TipoResultadoVotacao, TipoSessaoPlenaria, VotoParlamentar)

TipoSessaoCrud = CrudAux.build(TipoSessaoPlenaria, 'tipo_sessao_plenaria')
TipoExpedienteCrud = CrudAux.build(TipoExpediente, 'tipo_expediente')
CargoBancadaCrud = CrudAux.build(CargoBancada, '')


TipoResultadoVotacaoCrud = CrudAux.build(
    TipoResultadoVotacao, 'tipo_resultado_votacao')


def reordernar_materias_expediente(request, pk):
    expedientes = ExpedienteMateria.objects.filter(
        sessao_plenaria_id=pk)
    for exp_num, e in enumerate(expedientes, 1):
        e.numero_ordem = exp_num
        e.save()

    return HttpResponseRedirect(
        reverse('sapl.sessao:expedientemateria_list', kwargs={'pk': pk}))


def reordernar_materias_ordem(request, pk):
    ordens = OrdemDia.objects.filter(
        sessao_plenaria_id=pk)
    for ordem_num, o in enumerate(ordens, 1):
        o.numero_ordem = ordem_num
        o.save()

    return HttpResponseRedirect(
        reverse('sapl.sessao:ordemdia_list', kwargs={'pk': pk}))


def verifica_presenca(request, model, spk):
    if not model.objects.filter(sessao_plenaria_id=spk).exists():
        msg = _('Votação não pode ser aberta sem presenças')
        messages.add_message(request, messages.ERROR, msg)
        return False
    return True


def verifica_votacoes_abertas(request):
    votacoes_abertas = SessaoPlenaria.objects.filter(
        Q(ordemdia__votacao_aberta=True) |
        Q(expedientemateria__votacao_aberta=True)).distinct()

    if votacoes_abertas:
        msg_abertas = []
        for v in votacoes_abertas:
            msg_abertas.append('''<li><a href="%s">%s</a></li>''' % (
                reverse('sapl.sessao:sessaoplenaria_detail',
                        kwargs={'pk': v.id}),
                v.__str__()))

        msg = _('Já existem votações abertas nas seguintes Sessões: ' +
                ', '.join(msg_abertas) + '. Para abrir '
                'outra, termine ou feche as votações abertas.')
        messages.add_message(request, messages.INFO, msg)

        return False

    return True


def verifica_sessao_iniciada(request, spk):
    sessao = SessaoPlenaria.objects.get(id=spk)

    if not sessao.iniciada or sessao.finalizada:
        msg = _('Não é possível abrir matérias para votação. '
                'Esta Sessão Plenária não foi iniciada ou está finalizada.')
        messages.add_message(request, messages.INFO, msg)
        return False

    return True


@permission_required('sessao.change_expedientemateria',
                     'sessao.change_ordemdia')
def abrir_votacao(request, pk, spk):
    model = None

    if 'tipo_materia' in request.GET:
        if request.GET['tipo_materia'] == 'ordem':
            model = OrdemDia
            presenca_model = PresencaOrdemDia
            redirect_url = 'ordemdia_list'
        elif request.GET['tipo_materia'] == 'expediente':
            model = ExpedienteMateria
            presenca_model = SessaoPlenariaPresenca
            redirect_url = 'expedientemateria_list'
    if not model:
        raise Http404

    if (verifica_presenca(request, presenca_model, spk) and
        verifica_votacoes_abertas(request) and
            verifica_sessao_iniciada(request, spk)):
        materia_votacao = model.objects.get(id=pk)
        materia_votacao.votacao_aberta = True
        sessao = SessaoPlenaria.objects.get(id=spk)
        sessao.painel_aberto = True
        sessao.save()
        materia_votacao.save()

    return HttpResponseRedirect(
        reverse('sapl.sessao:' + redirect_url, kwargs={'pk': spk}))


def customize_link_materia(context, pk):
    for i, row in enumerate(context['rows']):
        materia = context['object_list'][i].materia
        url_materia = reverse('sapl.materia:materialegislativa_detail',
                              kwargs={'pk': materia.id})
        numeracao = materia.numeracao_set.first()
        autoria = materia.autoria_set.filter(
            primeiro_autor=True).first()
        autor = autoria.autor if autoria else None
        num_protocolo = materia.numero_protocolo

        data_inicio_sessao = SessaoPlenaria.objects.get(id=pk).data_inicio

        tramitacao = Tramitacao.objects.filter(materia=materia,
                                               turno__isnull=False,
                                               data_tramitacao__lte=data_inicio_sessao
                                               ).exclude(turno__exact=''
                                                         ).select_related(
            'materia',
            'status',
            'materia__tipo').order_by(
            '-data_tramitacao'
        ).first()
        turno = '  '
        if tramitacao is not None:
            for t in Tramitacao.TURNO_CHOICES:
                if t[0] == tramitacao.turno:
                    turno = t[1]
                    break

        title_materia = '''<a href=%s>%s</a> </br>
                           <b>Processo:</b> %s </br>
                           <b>Autor:</b> %s </br>
                           <b>Protocolo:</b> %s </br>
                           <b>Turno:</b> %s </br>
                        ''' % (url_materia,
                               row[1][0],
                               numeracao if numeracao else '',
                               autor if autor else '',
                               num_protocolo if num_protocolo else '',
                               turno)

        # Na linha abaixo, o segundo argumento é None para não colocar
        # url em toda a string de title_materia
        context['rows'][i][1] = (title_materia, None)
    return context


def get_presencas_generic(model, sessao, legislatura):
    presencas = model.objects.filter(
        sessao_plenaria=sessao)

    presentes = [p.parlamentar for p in presencas]

    mandato = Mandato.objects.filter(
        legislatura=legislatura).order_by('parlamentar__nome_parlamentar')

    for m in mandato:
        if m.parlamentar in presentes:
            yield (m.parlamentar, True)
        else:
            yield (m.parlamentar, False)


class MateriaOrdemDiaCrud(MasterDetailCrud):
    model = OrdemDia
    parent_field = 'sessao_plenaria'
    help_topic = 'sessao_plenaria_materias_ordem_dia'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['numero_ordem', 'materia', 'materia__ementa',
                            'resultado']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = OrdemDiaForm

        def get_initial(self):
            self.initial['data_ordem'] = SessaoPlenaria.objects.get(
                pk=self.kwargs['pk']).data_inicio.strftime('%d/%m/%Y')
            max_numero_ordem = OrdemDia.objects.filter(
                sessao_plenaria=self.kwargs['pk']).aggregate(
                    Max('numero_ordem'))['numero_ordem__max']
            self.initial['numero_ordem'] = (
                max_numero_ordem if max_numero_ordem else 0) + 1
            return self.initial

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
        paginate_by = None
        ordering = ['numero_ordem', 'materia', 'resultado']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            return customize_link_materia(context, self.kwargs['pk'])

        def get_rows(self, object_list):
            for obj in object_list:
                exist_resultado = obj.registrovotacao_set.filter(
                    materia=obj.materia).exists()
                if not exist_resultado:
                    if obj.votacao_aberta:
                        url = ''
                        if obj.tipo_votacao == 1:
                            url = reverse('sapl.sessao:votacaosimbolica',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})
                        elif obj.tipo_votacao == 2:
                            url = reverse('sapl.sessao:votacaonominal',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})
                        elif obj.tipo_votacao == 3:
                            url = reverse('sapl.sessao:votacaosecreta',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})
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
                            'pk': obj.pk,
                            'spk': obj.sessao_plenaria_id
                        }) + '?tipo_materia=ordem'

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
                    resultado = obj.registrovotacao_set.get(
                        materia_id=obj.materia_id)
                    resultado_descricao = resultado.tipo_resultado_votacao.nome
                    resultado_observacao = resultado.observacao

                    if self.request.user.has_module_perms(AppConfig.label):
                        url = ''
                        if obj.tipo_votacao == 1:
                            url = reverse('sapl.sessao:votacaosimbolicaedit',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})
                        elif obj.tipo_votacao == 2:
                            url = reverse('sapl.sessao:votacaonominaledit',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})
                        elif obj.tipo_votacao == 3:
                            url = reverse('sapl.sessao:votacaosecretaedit',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})
                        obj.resultado = ('<a href="%s">%s<br/>%s</a>' %
                                         (url,
                                          resultado_descricao,
                                          resultado_observacao))
                    else:
                        if obj.tipo_votacao == 2:
                            url = reverse(
                                'sapl.sessao:votacao_nominal_transparencia',
                                kwargs={
                                    'pk': obj.sessao_plenaria_id,
                                    'oid': obj.pk,
                                    'mid': obj.materia_id}) +\
                                '?&materia=ordem'
                            obj.resultado = ('<a href="%s">%s<br/>%s</a>' %
                                             (url,
                                              resultado_descricao,
                                              resultado_observacao))
                        else:
                            obj.resultado = ('%s<br/>%s' %
                                             (resultado_descricao,
                                              resultado_observacao))

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
    help_topic = 'sessao_plenaria_materia_expediente'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['numero_ordem', 'materia',
                            'materia__ementa', 'resultado']

    class ListView(MasterDetailCrud.ListView):
        paginate_by = None
        ordering = ['numero_ordem', 'materia', 'resultado']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            return customize_link_materia(context, self.kwargs['pk'])

        def get_rows(self, object_list):
            for obj in object_list:
                exist_resultado = obj.registrovotacao_set.filter(
                    materia=obj.materia).exists()

                if not exist_resultado:
                    if obj.votacao_aberta:
                        url = ''
                        if obj.tipo_votacao == 1:
                            url = reverse('sapl.sessao:votacaosimbolicaexp',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})
                        elif obj.tipo_votacao == 2:
                            url = reverse('sapl.sessao:votacaonominalexp',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})
                        elif obj.tipo_votacao == 3:
                            url = reverse('sapl.sessao:votacaosecretaexp',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})

                        if self.request.user.has_module_perms(AppConfig.label):
                            btn_registrar = '''
                                <a href="%s" class="btn btn-primary"
                                   role="button">
                                   Registrar Votação</a>''' % (url)
                            obj.resultado = btn_registrar
                    else:
                        url = reverse('sapl.sessao:abrir_votacao', kwargs={
                            'pk': obj.pk,
                            'spk': obj.sessao_plenaria_id
                        }) + '?tipo_materia=expediente'
                        btn_abrir = '''Matéria não votada<br />'''

                        if self.request.user.has_module_perms(AppConfig.label):
                            btn_abrir += '''
                            <a href="%s"
                               class="btn btn-primary"
                               role="button">Abrir Votação</a>''' % (url)

                        obj.resultado = btn_abrir
                else:
                    url = ''
                    resultado = obj.registrovotacao_set.get(
                        materia_id=obj.materia_id)
                    resultado_descricao = resultado.tipo_resultado_votacao.nome
                    resultado_observacao = resultado.observacao
                    if self.request.user.has_module_perms(AppConfig.label):
                        if obj.tipo_votacao == 1:
                            url = reverse(
                                'sapl.sessao:votacaosimbolicaexpedit',
                                kwargs={
                                    'pk': obj.sessao_plenaria_id,
                                    'oid': obj.pk,
                                    'mid': obj.materia_id})
                        elif obj.tipo_votacao == 2:
                            url = reverse('sapl.sessao:votacaonominalexpedit',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})
                        elif obj.tipo_votacao == 3:
                            url = reverse('sapl.sessao:votacaosecretaexpedit',
                                          kwargs={
                                              'pk': obj.sessao_plenaria_id,
                                              'oid': obj.pk,
                                              'mid': obj.materia_id})
                        obj.resultado = ('<a href="%s">%s<br/>%s</a>' %
                                         (url,
                                          resultado_descricao,
                                          resultado_observacao))
                    else:
                        if obj.tipo_votacao == 2:
                            url = reverse(
                                'sapl.sessao:votacao_nominal_transparencia',
                                kwargs={
                                    'pk': obj.sessao_plenaria_id,
                                    'oid': obj.pk,
                                    'mid': obj.materia_id}) +\
                                '?&materia=expediente'
                            obj.resultado = ('<a href="%s">%s<br/>%s</a>' %
                                             (url,
                                              resultado_descricao,
                                              resultado_observacao))
                        else:
                            obj.resultado = ('%s<br/>%s' %
                                             (resultado_descricao,
                                              resultado_observacao))
            return [self._as_row(obj) for obj in object_list]

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ExpedienteMateriaForm

        def get_initial(self):
            self.initial['data_ordem'] = SessaoPlenaria.objects.get(
                pk=self.kwargs['pk']).data_inicio.strftime('%d/%m/%Y')
            max_numero_ordem = ExpedienteMateria.objects.filter(
                sessao_plenaria=self.kwargs['pk']).aggregate(
                    Max('numero_ordem'))['numero_ordem__max']
            self.initial['numero_ordem'] = (
                max_numero_ordem if max_numero_ordem else 0) + 1
            return self.initial

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
    help_topic = 'sessao_plenaria_oradores'
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


class BancadaCrud(Crud):
    model = Bancada

    class CreateView(Crud.CreateView):
        form_class = BancadaForm

        def get_success_url(self):
            return reverse('sapl.sessao:bancada_list')


class BlocoCrud(Crud):
    model = Bloco

    class CreateView(Crud.CreateView):
        form_class = BlocoForm

        def get_success_url(self):
            return reverse('sapl.sessao:bloco_list')


def recuperar_numero_sessao(request):
    try:
        sessao = SessaoPlenaria.objects.filter(
            tipo__pk=request.GET['tipo'],
            sessao_legislativa=request.GET['sessao_legislativa']).last()
    except ObjectDoesNotExist:
        numero = 1
    else:
        if sessao:
            numero = sessao.numero + 1
        else:
            numero = 1

    return JsonResponse({'numero': numero})


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
    help_topic = 'sessao_legislativa'
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

    class UpdateView(Crud.UpdateView):

        form_class = SessaoPlenariaForm

        def get_initial(self):
            return {'sessao_legislativa': self.object.sessao_legislativa}

    class CreateView(Crud.CreateView):

        form_class = SessaoPlenariaForm

        @property
        def cancel_url(self):
            return self.search_url

        def get_initial(self):
            legislatura = Legislatura.objects.order_by('-data_inicio').first()
            if legislatura:
                return {
                    'legislatura': legislatura,
                    'sessao_legislativa': legislatura.sessaoplenaria_set.first(
                    )}
            else:
                msg = _('Cadastre alguma legislatura antes de adicionar ' +
                        'uma sessão plenária!')
                messages.add_message(self.request, messages.ERROR, msg)
                return {}

    class DeleteView(Crud.DeleteView, RedirectView):

        def get_success_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'sessaoplenaria_list'))


class SessaoPermissionMixin(PermissionRequiredForAppCrudMixin,
                            FormMixin,
                            DetailView):
    model = SessaoPlenaria
    app_label = AppConfig.label,


class PresencaMixin:

    def get_presencas(self):
        return get_presencas_generic(
            SessaoPlenariaPresenca,
            self.object,
            self.object.legislatura)

    def get_presencas_ordem(self):
        return get_presencas_generic(
            PresencaOrdemDia,
            self.object,
            self.object.legislatura)


class PresencaView(FormMixin, PresencaMixin, DetailView):
    template_name = 'sessao/presenca.html'
    form_class = PresencaForm
    model = SessaoPlenaria

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Presença'), self.object)
        return context

    @method_decorator(permission_required(
        'sessao.add_sessaoplenariapresenca'))
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            # Pegar os presentes salvos no banco
            presentes_banco = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=self.object.id).values_list(
                'parlamentar_id', flat=True).distinct()

            # Id dos parlamentares presentes
            marcados = request.POST.getlist('presenca_ativos') \
                + request.POST.getlist('presenca_inativos')

            # Deletar os que foram desmarcados
            deletar = set(presentes_banco) - set(marcados)
            SessaoPlenariaPresenca.objects.filter(
                parlamentar_id__in=deletar,
                sessao_plenaria_id=self.object.id).delete()

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

    def get(self, request, *args, **kwargs):
        if request.user.is_anonymous():
            self.template_name = 'painel/index.html'

        request.session['discurso'] = 'stop'
        request.session['aparte'] = 'stop'
        request.session['ordem'] = 'stop'

        return TemplateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        cronometro_discurso = AppsAppConfig.attr('cronometro_discurso')
        cronometro_aparte = AppsAppConfig.attr('cronometro_aparte')
        cronometro_ordem = AppsAppConfig.attr('cronometro_ordem')

        if (not cronometro_discurso or not cronometro_aparte
                or not cronometro_ordem):
            msg = _(
                'Você precisa primeiro configurar os cronômetros \
                nas Configurações da Aplicação')
            messages.add_message(self.request, messages.ERROR, msg)

        else:
            m, s, x = cronometro_discurso.isoformat().split(':')
            cronometro_discurso = int(m) * 60 + int(s)

            m, s, x = cronometro_aparte.isoformat().split(':')
            cronometro_aparte = int(m) * 60 + int(s)

            m, s, x = cronometro_ordem.isoformat().split(':')
            cronometro_ordem = int(m) * 60 + int(s)

        context = TemplateView.get_context_data(self, **kwargs)
        context.update({
            'head_title': str(_('Painel Plenário')),
            'sessao_id': kwargs['pk'],
            'root_pk': kwargs['pk'],
            'sessaoplenaria': SessaoPlenaria.objects.get(pk=kwargs['pk']),
            'cronometro_discurso': cronometro_discurso,
            'cronometro_aparte': cronometro_aparte,
            'cronometro_ordem': cronometro_ordem})

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

    @method_decorator(permission_required('sessao.add_presencaordemdia'))
    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            # Pegar os presentes salvos no banco
            presentes_banco = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=self.object.id).values_list(
                'parlamentar_id', flat=True).distinct()

            # Id dos parlamentares presentes
            marcados = request.POST.getlist('presenca_ativos') \
                + request.POST.getlist('presenca_inativos')

            # Deletar os que foram desmarcados
            deletar = set(presentes_banco) - set(marcados)
            PresencaOrdemDia.objects.filter(
                parlamentar_id__in=deletar,
                sessao_plenaria_id=self.object.id).delete()

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
            ementa = o.materia.ementa
            titulo = o.materia
            numero = o.numero_ordem

            autoria = Autoria.objects.filter(materia_id=o.materia_id)
            autor = [str(a.autor) for a in autoria]

            mat = {'pk': pk,
                   'oid': o.id,
                   'ordem_id': o.materia_id,
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

    @method_decorator(permission_required('sessao.change_ordemdia'))
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
                    ementa = o.materia.ementa
                    titulo = o.materia
                    numero = o.numero_ordem

                    autoria = Autoria.objects.filter(materia_id=o.materia_id)
                    autor = [str(a.autor) for a in autoria]

                    mat = {'pk': pk,
                           'oid': o.id,
                           'ordem_id': o.materia_id,
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

        try:
            sessao = SessaoPlenaria.objects.get(
                id=kwargs['pk'])
        except ObjectDoesNotExist:
            mensagem = _('Esta Sessão Plenária não existe!')
            messages.add_message(request, messages.INFO, mensagem)

            return self.render_to_response(context)

        mesa = sessao.integrantemesa_set.all() if sessao else []

        cargos_ocupados = [m.cargo for m in mesa]
        cargos = CargoMesa.objects.all()
        cargos_vagos = list(set(cargos) - set(cargos_ocupados))

        parlamentares = Legislatura.objects.first().mandato_set.all()
        parlamentares_ocupados = [m.parlamentar for m in mesa]
        parlamentares_vagos = list(
            set(
                [p.parlamentar for p in parlamentares]) - set(
                parlamentares_ocupados))

        # Se todos os cargos estiverem ocupados, a listagem de parlamentares
        # deve ser renderizada vazia
        if not cargos_vagos:
            parlamentares_vagos = []

        context.update(
            {'composicao_mesa': mesa,
             'parlamentares': parlamentares_vagos,
             'cargos_vagos': cargos_vagos})

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = FormMixin.get_context_data(self, **kwargs)
        context['title'] = '%s <small>(%s)</small>' % (
            _('Mesa Diretora'), self.object)
        return context

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:mesa', kwargs={'pk': pk})


def atualizar_mesa(request):
    """
        Esta função lida com qualquer alteração nos campos
        da Mesa Diretora, atualizando os campos após cada alteração
    """
    try:
        sessao = SessaoPlenaria.objects.get(
            id=int(request.GET['sessao']))
    except ObjectDoesNotExist:
        return JsonResponse({'msg': ('Sessão Inexistente!', 0)})

    # Atualiza os componentes da view após a mudança
    composicao_mesa = IntegranteMesa.objects.filter(
        sessao_plenaria=sessao.id)

    cargos_ocupados = [m.cargo for m in composicao_mesa]
    cargos = CargoMesa.objects.all()
    cargos_vagos = list(set(cargos) - set(cargos_ocupados))

    parlamentares = Legislatura.objects.get(
        id=sessao.legislatura.id).mandato_set.all()
    parlamentares_ocupados = [m.parlamentar for m in composicao_mesa]
    parlamentares_vagos = list(
        set(
            [p.parlamentar for p in parlamentares]) - set(
            parlamentares_ocupados))

    lista_composicao = [(c.id, c.parlamentar.__str__(),
                         c.cargo.__str__()) for c in composicao_mesa]
    lista_parlamentares = [(
        p.id, p.__str__()) for p in parlamentares_vagos]
    lista_cargos = [(c.id, c.__str__()) for c in cargos_vagos]

    return JsonResponse(
        {'lista_composicao': lista_composicao,
         'lista_parlamentares': lista_parlamentares,
         'lista_cargos': lista_cargos,
         'msg': ('', 1)})


def insere_parlamentar_composicao(request):
    """
        Esta função lida com qualquer operação de inserção
        na composição da Mesa Diretora
    """
    if request.user.has_perm(
            '%s.add_%s' % (
                AppConfig.label, IntegranteMesa._meta.model_name)):

        composicao = IntegranteMesa()

        try:
            composicao.sessao_plenaria = SessaoPlenaria.objects.get(
                id=int(request.POST['sessao']))
        except MultiValueDictKeyError:
            return JsonResponse({'msg': ('A Sessão informada não existe!', 0)})

        try:
            composicao.parlamentar = Parlamentar.objects.get(
                id=int(request.POST['parlamentar']))
        except MultiValueDictKeyError:
            return JsonResponse({
                'msg': ('Nenhum parlamentar foi inserido!', 0)})

        try:
            composicao.cargo = CargoMesa.objects.get(
                id=int(request.POST['cargo']))
            parlamentar_ja_inserido = IntegranteMesa.objects.filter(
                sessao_plenaria_id=composicao.sessao_plenaria.id,
                cargo_id=composicao.cargo.id).exists()

            if parlamentar_ja_inserido:
                return JsonResponse({'msg': ('Parlamentar já inserido!', 0)})

            composicao.save()

        except MultiValueDictKeyError:
            return JsonResponse({'msg': ('Nenhum cargo foi inserido!', 0)})

        return JsonResponse({'msg': ('Parlamentar inserido com sucesso!', 1)})

    else:
        return JsonResponse(
            {'msg': ('Você não tem permissão para esta operação!', 0)})


def remove_parlamentar_composicao(request):
    """
        Essa função lida com qualquer operação de remoção
        na composição da Mesa Diretora
    """
    if request.POST and request.user.has_perm(
        '%s.delete_%s' % (
            AppConfig.label, IntegranteMesa._meta.model_name)):

        if 'composicao_mesa' in request.POST:
            try:
                composicao = IntegranteMesa.objects.get(
                    id=int(request.POST['composicao_mesa']))
            except ObjectDoesNotExist:
                return JsonResponse(
                    {'msg': (
                        'Composição da Mesa não pôde ser removida!', 0)})

            composicao.delete()

            return JsonResponse(
                {'msg': (
                    'Parlamentar excluido com sucesso!', 1)})
        else:
            return JsonResponse(
                {'msg': (
                    'Selecione algum parlamentar para ser excluido!', 0)})


class ResumoOrdenacaoView(PermissionRequiredMixin, FormView):
    template_name = 'sessao/resumo_ordenacao.html'
    form_class = ResumoOrdenacaoForm
    permission_required = {'sessao.change_resumoordenacao'}

    def get_success_url(self):
        return reverse('sapl.base:sistema')

    def get_initial(self):
        ordenacao = ResumoOrdenacao.objects.first()
        if ordenacao:
            return {'primeiro': ordenacao.primeiro,
                    'segundo': ordenacao.segundo,
                    'terceiro': ordenacao.terceiro,
                    'quarto': ordenacao.quarto,
                    'quinto': ordenacao.quinto,
                    'sexto': ordenacao.sexto,
                    'setimo': ordenacao.setimo,
                    'oitavo': ordenacao.oitavo,
                    'nono': ordenacao.nono,
                    'decimo': ordenacao.decimo}
        return self.initial.copy()

    def form_valid(self, form):
        ordenacao = ResumoOrdenacao.objects.get_or_create()[0]

        ordenacao.primeiro = form.cleaned_data['primeiro']
        ordenacao.segundo = form.cleaned_data['segundo']
        ordenacao.terceiro = form.cleaned_data['terceiro']
        ordenacao.quarto = form.cleaned_data['quarto']
        ordenacao.quinto = form.cleaned_data['quinto']
        ordenacao.sexto = form.cleaned_data['sexto']
        ordenacao.setimo = form.cleaned_data['setimo']
        ordenacao.oitavo = form.cleaned_data['oitavo']
        ordenacao.nono = form.cleaned_data['nono']
        ordenacao.decimo = form.cleaned_data['decimo']

        ordenacao.save()

        return HttpResponseRedirect(self.get_success_url())


def get_turno(turno):
    for i in Tramitacao.TURNO_CHOICES:
        if i[0] == turno:
            return str(i[1])
    else:
        return ''


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
        encerramento = data_fim.strftime('%d/%m/%Y') + ' -' if data_fim else ''

        context.update({'basica': [
            _('Tipo de Sessão: %(tipo)s') % {'tipo': self.object.tipo},
            _('Abertura: %(abertura)s - %(hora_inicio)s') % {
                'abertura': abertura, 'hora_inicio': self.object.hora_inicio},
            _('Encerramento: %(encerramento)s %(hora_fim)s') % {
                'encerramento': encerramento, 'hora_fim': self.object.hora_fim}
        ]})
        # =====================================================================
        # Conteúdo Multimídia
        if self.object.url_audio:
            context.update({'multimidia_audio':
                            _('Audio: ') + str(self.object.url_audio)})
        else:
            context.update({'multimidia_audio': _('Audio: Indisponível')})

        if self.object.url_video:
            context.update({'multimidia_video':
                            _('Video: ') + str(self.object.url_video)})
        else:
            context.update({'multimidia_video': _('Video: Indisponível')})

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
        ).order_by('parlamentar__nome_parlamentar')

        parlamentares_sessao = [p.parlamentar for p in presencas]

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

            ementa = m.materia.ementa
            titulo = m.materia
            numero = m.numero_ordem
            tramitacao = m.materia.tramitacao_set.last()
            turno = None
            if tramitacao:
                turno = get_turno(tramitacao.turno)

            rv = m.registrovotacao_set.first()
            if rv:
                resultado = rv.tipo_resultado_votacao.nome
                resultado_observacao = rv.observacao

            else:
                resultado = _('Matéria não votada')
                resultado_observacao = _(' ')

            autoria = Autoria.objects.filter(materia_id=m.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'turno': turno,
                   'resultado': resultado,
                   'resultado_observacao': resultado_observacao,
                   'autor': autor,
                   'numero_protocolo': m.materia.numero_protocolo,
                   'numero_processo': m.materia.numeracao_set.last()
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
        ).order_by('parlamentar__nome_parlamentar')

        parlamentares_ordem = [p.parlamentar for p in presencas]

        context.update({'presenca_ordem': parlamentares_ordem})

        # =====================================================================
        # Matérias Ordem do Dia
        ordem = OrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id)
        materias_ordem = []
        for o in ordem:
            ementa = o.materia.ementa
            titulo = o.materia
            numero = o.numero_ordem
            tramitacao = o.materia.tramitacao_set.last()
            turno = None
            if tramitacao:
                turno = get_turno(tramitacao.turno)

            # Verificar resultado
            rv = o.registrovotacao_set.filter(materia=o.materia).first()
            if rv:
                resultado = rv.tipo_resultado_votacao.nome
                resultado_observacao = rv.observacao
            else:
                resultado = _('Matéria não votada')
                resultado_observacao = _(' ')

            autoria = Autoria.objects.filter(
                materia_id=o.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'turno': turno,
                   'resultado': resultado,
                   'resultado_observacao': resultado_observacao,
                   'autor': autor,
                   'numero_protocolo': o.materia.numero_protocolo,
                   'numero_processo': o.materia.numeracao_set.last()
                   }
            materias_ordem.append(mat)

        context.update({'materias_ordem': materias_ordem})

        # =====================================================================
        # Oradores nas Explicações Pessoais
        oradores_explicacoes = []
        for orador in Orador.objects.filter(
                sessao_plenaria_id=self.object.id).order_by('numero_ordem'):
            for parlamentar in Parlamentar.objects.filter(
                    id=orador.parlamentar.id):
                partido_sigla = Filiacao.objects.filter(
                    parlamentar=parlamentar).last()
                if not partido_sigla:
                    sigla = ''
                else:
                    sigla = partido_sigla.partido.sigla
                oradores = {
                    'numero_ordem': orador.numero_ordem,
                    'parlamentar': parlamentar,
                    'sgl_partido': sigla
                }
                oradores_explicacoes.append(oradores)
        context.update({'oradores_explicacoes': oradores_explicacoes})

        # =====================================================================
        # Indica a ordem com a qual o template será renderizado
        ordenacao = ResumoOrdenacao.objects.first()
        dict_ord_template = {
            'cont_mult': 'conteudo_multimidia.html',
            'exp': 'expedientes.html',
            'id_basica': 'identificacao_basica.html',
            'lista_p': 'lista_presenca.html',
            'lista_p_o_d': 'lista_presenca_ordem_dia.html',
            'mat_exp': 'materias_expediente.html',
            'mat_o_d': 'materias_ordem_dia.html',
            'mesa_d': 'mesa_diretora.html',
            'oradores_exped': 'oradores_expediente.html',
            'oradores_expli': 'oradores_explicacoes.html'
        }

        if ordenacao:
            context.update(
                {'primeiro_ordenacao': dict_ord_template[ordenacao.primeiro],
                 'segundo_ordenacao': dict_ord_template[ordenacao.segundo],
                 'terceiro_ordenacao': dict_ord_template[ordenacao.terceiro],
                 'quarto_ordenacao': dict_ord_template[ordenacao.quarto],
                 'quinto_ordenacao': dict_ord_template[ordenacao.quinto],
                 'sexto_ordenacao': dict_ord_template[ordenacao.sexto],
                 'setimo_ordenacao': dict_ord_template[ordenacao.setimo],
                 'oitavo_ordenacao': dict_ord_template[ordenacao.oitavo],
                 'nono_ordenacao': dict_ord_template[ordenacao.nono],
                 'decimo_ordenacao': dict_ord_template[ordenacao.decimo]})
        else:
            context.update(
                {'primeiro_ordenacao': dict_ord_template['id_basica'],
                 'segundo_ordenacao': dict_ord_template['cont_mult'],
                 'terceiro_ordenacao': dict_ord_template['mesa_d'],
                 'quarto_ordenacao': dict_ord_template['lista_p'],
                 'quinto_ordenacao': dict_ord_template['exp'],
                 'sexto_ordenacao': dict_ord_template['mat_exp'],
                 'setimo_ordenacao': dict_ord_template['oradores_exped'],
                 'oitavo_ordenacao': dict_ord_template['lista_p_o_d'],
                 'nono_ordenacao': dict_ord_template['mat_o_d'],
                 'decimo_ordenacao': dict_ord_template['oradores_expli']})

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

    @method_decorator(permission_required('sessao.add_expedientesessao'))
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

        materia_id = kwargs['mid']
        ordem_id = kwargs['oid']

        if(int(request.POST['anular_votacao']) == 1):
            for r in RegistroVotacao.objects.filter(ordem_id=ordem_id):
                r.delete()

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

        materia_id = kwargs['mid']
        ordem_id = kwargs['oid']

        ordem = OrdemDia.objects.get(id=ordem_id)

        materia = {'materia': ordem.materia, 'ementa': ordem.materia.ementa}
        context.update({'materia': materia})

        votacao = RegistroVotacao.objects.filter(
            materia_id=materia_id,
            ordem_id=ordem_id).last()
        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'resultado': votacao.tipo_resultado_votacao.nome,
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

    """
        Votação Simbólica e Secreta
    """

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

        ordem_id = kwargs['oid']
        ordem = OrdemDia.objects.get(id=ordem_id)
        qtde_presentes = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': ordem.materia, 'ementa': ordem.materia.ementa}
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

        ordem_id = kwargs['oid']
        ordem = OrdemDia.objects.get(id=ordem_id)
        qtde_presentes = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': ordem.materia, 'ementa': ordem.materia.ementa}
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
            materia_id = kwargs['mid']
            ordem_id = kwargs['oid']

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


def fechar_votacao_materia(materia):
    if type(materia) == OrdemDia:
        registro_votacao = RegistroVotacao.objects.filter(ordem=materia)
        voto_parlamentar = VotoParlamentar.objects.filter(ordem=materia)

    elif type(materia) == ExpedienteMateria:
        registro_votacao = RegistroVotacao.objects.filter(
            expediente=materia)
        voto_parlamentar = VotoParlamentar.objects.filter(expediente=materia)

    for v in voto_parlamentar:
        v.delete()

    for r in registro_votacao:
        r.delete()

    if materia.resultado:
        materia.resultado = ''
    materia.votacao_aberta = False
    materia.save()


class VotacaoNominalAbstract(SessaoPermissionMixin):
    template_name = 'sessao/votacao/nominal.html'
    ordem = None
    expediente = None
    form_class = VotacaoNominalForm

    def get(self, request, *args, **kwargs):
        if self.ordem:
            ordem_id = kwargs['oid']
            if RegistroVotacao.objects.filter(ordem_id=ordem_id).exists():
                msg = _('Esta matéria já foi votada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(reverse(
                    'sapl.sessao:ordemdia_list', kwargs={'pk': kwargs['pk']}))

            try:
                ordem = OrdemDia.objects.get(id=ordem_id)
            except ObjectDoesNotExist:
                raise Http404()

            presentes = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=ordem.sessao_plenaria_id)
            total = presentes.count()

            materia_votacao = ordem

        elif self.expediente:
            expediente_id = kwargs['oid']
            if (RegistroVotacao.objects.filter(
               expediente_id=expediente_id).exists()):
                msg = _('Esta matéria já foi votada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(reverse(
                    'sapl.sessao:expedientemateria_list',
                    kwargs={'pk': kwargs['pk']}))

            try:
                expediente = ExpedienteMateria.objects.get(id=expediente_id)
            except ObjectDoesNotExist:
                raise Http404()

            presentes = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=expediente.sessao_plenaria_id)
            total = presentes.count()

            materia_votacao = expediente

        materia = {'materia': materia_votacao.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(
                           materia_votacao.materia.ementa))}
        context = {'materia': materia, 'object': self.get_object(),
                   'parlamentares': self.get_parlamentares(presentes),
                   'form': self.get_form(),
                   'total': total}

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if self.ordem:
            ordem_id = kwargs['oid']
            try:
                materia_votacao = OrdemDia.objects.get(id=ordem_id)
            except ObjectDoesNotExist:
                raise Http404()
        elif self.expediente:
            expediente_id = kwargs['oid']
            try:
                materia_votacao = ExpedienteMateria.objects.get(id=expediente_id)
            except ObjectDoesNotExist:
                raise Http404()

        if 'cancelar-votacao' in request.POST:
            fechar_votacao_materia(materia_votacao)
            return self.form_valid(form)

        if form.is_valid():
            votos_sim = 0
            votos_nao = 0
            abstencoes = 0
            nao_votou = 0

            for votos in request.POST.getlist('voto_parlamentar'):
                v = votos.split(':')
                voto = v[0]
                parlamentar_id = v[1]

                if voto == 'Sim':
                    votos_sim += 1
                elif voto == 'Não':
                    votos_nao += 1
                elif voto == 'Abstenção':
                    abstencoes += 1
                elif voto == 'Não Votou':
                    nao_votou += 1

            # Caso todas as opções sejam 'Não votou', fecha a votação
            if nao_votou == len(request.POST.getlist('voto_parlamentar')):
                form.add_error(None, 'Não é possível finalizar a votação sem '
                                     'nenhum voto')
                return self.form_invalid(form)

            if self.ordem:
                votacao = RegistroVotacao.objects.filter(
                    ordem_id=ordem_id)
            elif self.expediente:
                votacao = RegistroVotacao.objects.filter(
                    expediente_id=expediente_id)

            # Remove todas as votação desta matéria, caso existam
            for v in votacao:
                v.delete()

            votacao = RegistroVotacao()
            votacao.numero_votos_sim = votos_sim
            votacao.numero_votos_nao = votos_nao
            votacao.numero_abstencoes = abstencoes
            votacao.observacao = request.POST.get('observacao', None)

            votacao.materia_id = materia_votacao.materia.id
            if self.ordem:
                votacao.ordem_id = ordem_id
            elif self.expediente:
                votacao.expediente_id = expediente_id

            votacao.tipo_resultado_votacao = form.cleaned_data['resultado_votacao']
            votacao.save()

            for votos in request.POST.getlist('voto_parlamentar'):
                v = votos.split(':')
                voto = v[0]
                parlamentar_id = v[1]

                if self.ordem:
                    voto_parlamentar = VotoParlamentar.objects.get_or_create(
                        parlamentar_id=parlamentar_id,
                        ordem_id=ordem_id)[0]
                elif self.expediente:
                    voto_parlamentar = VotoParlamentar.objects.get_or_create(
                        parlamentar_id=parlamentar_id,
                        expediente_id=expediente_id)[0]

                voto_parlamentar.voto = voto
                voto_parlamentar.parlamentar_id = parlamentar_id
                voto_parlamentar.votacao_id = votacao.id
                voto_parlamentar.save()

                resultado = form.cleaned_data['resultado_votacao']

                materia_votacao.resultado = resultado.nome
                materia_votacao.votacao_aberta = False
                materia_votacao.save()

            # Verifica se existe algum VotoParlamentar sem RegistroVotacao
            # Por exemplo, se algum parlamentar votar e sua presença for
            # removida da ordem do dia/expediente antes da conclusão da
            # votação
            if self.ordem:
                VotoParlamentar.objects.filter(
                    ordem_id=ordem_id,
                    votacao__isnull=True).delete()
            elif self.expediente:
                VotoParlamentar.objects.filter(
                    expediente_id=expediente_id,
                    votacao__isnull=True).delete()
            return self.form_valid(form)

        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        errors_tuple = [(form[e].label, form.errors[e]) for e in form.errors if e in form.fields]
        error_message = '''<ul>'''
        for e in errors_tuple:
            error_message += '''<li><b>%s</b>: %s</li>''' % (e[0], e[1][0])
        for e in form.non_field_errors():
            error_message += '''<li>%s</li>''' % e
        error_message += '''</ul>'''

        messages.add_message(self.request, messages.ERROR, error_message)

        if self.ordem:
            view = 'sapl.sessao:votacaonominal'
        elif self.expediente:
            view = 'sapl.sessao:votacaonominalexp'
        else:
            view = None

        return HttpResponseRedirect(reverse(
            view,
            kwargs={'pk': self.kwargs['pk'],
                    'oid': self.kwargs['oid'],
                    'mid': self.kwargs['mid']}))

    def get_parlamentares(self, presencas):
        self.object = self.get_object()

        presentes = [p.parlamentar for p in presencas]

        if self.ordem:
            voto_parlamentar = VotoParlamentar.objects.filter(
                ordem=self.kwargs['oid'])
        elif self.expediente:
            voto_parlamentar = VotoParlamentar.objects.filter(
                expediente=self.kwargs['oid'])

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                try:
                    voto = voto_parlamentar.get(
                        parlamentar=parlamentar)
                except ObjectDoesNotExist:
                    yield [parlamentar, None]
                else:
                    yield [parlamentar, voto.voto]

    def get_success_url(self):
        pk = self.kwargs['pk']

        if self.ordem:
            return reverse('sapl.sessao:ordemdia_list',
                           kwargs={'pk': pk})
        elif self.expediente:
            return reverse('sapl.sessao:expedientemateria_list',
                           kwargs={'pk': pk})


class VotacaoNominalEditAbstract(SessaoPermissionMixin):
    template_name = 'sessao/votacao/nominal_edit.html'

    def get(self, request, *args, **kwargs):
        context = {}

        if self.ordem:
            ordem_id = kwargs['oid']

            try:
                ordem = OrdemDia.objects.get(id=ordem_id)
                votacao = RegistroVotacao.objects.get(
                    ordem_id=ordem_id)
            except ObjectDoesNotExist:
                raise Http404()

            materia = ordem.materia
            ementa = ordem.materia.ementa

        elif self.expediente:
            expediente_id = kwargs['oid']

            try:
                expediente = ExpedienteMateria.objects.get(id=expediente_id)
                votacao = RegistroVotacao.objects.get(
                    expediente_id=expediente_id)
            except ObjectDoesNotExist:
                raise Http404()

            materia = expediente.materia
            ementa = expediente.materia.ementa

        votos = VotoParlamentar.objects.filter(votacao_id=votacao.id)

        list_votos = []
        for v in votos:
            parlamentar = Parlamentar.objects.get(id=v.parlamentar_id)
            list_votos.append({'parlamentar': parlamentar, 'voto': v.voto})

        context.update({'votos': list_votos})

        materia = {'materia': materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(ementa))}
        context.update({'materia': materia})

        votosSim = votosNao = abstencoes = naoRegistrados = 0
        for v in votos:
            if v.voto == 'Sim':
                votosSim += 1
            elif v.voto == 'Não':
                votosNao += 1
            elif v.voto == 'Abstenção':
                abstencoes += 1
            elif v.voto == 'Não Votou':
                naoRegistrados += 1

        list_contagem = {'votosSim': votosSim, 'votosNao': votosNao, 'abstencoes': abstencoes,
                         'naoRegistrados': naoRegistrados}

        context.update({'contagem': list_contagem})

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'resultado': votacao.tipo_resultado_votacao.nome,
            'tipo_resultado':
                votacao.tipo_resultado_votacao_id}
        context.update({'votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoEditForm(request.POST)

        if self.ordem:
            ordem_id = kwargs['oid']

            try:
                materia_votacao = OrdemDia.objects.get(id=ordem_id)
            except ObjectDoesNotExist:
                raise Http404()

        elif self.expediente:
            expediente_id = kwargs['oid']

            try:
                materia_votacao = ExpedienteMateria.objects.get(
                    id=expediente_id)
            except ObjectDoesNotExist:
                raise Http404()

        if(int(request.POST['anular_votacao']) == 1):
            fechar_votacao_materia(materia_votacao)

        return self.form_valid(form)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']

        if self.ordem:
            return reverse('sapl.sessao:ordemdia_list',
                           kwargs={'pk': pk})
        elif self.expediente:
            return reverse('sapl.sessao:expedientemateria_list',
                           kwargs={'pk': pk})


class VotacaoNominalView(VotacaoNominalAbstract):
    ordem = True
    expediente = False


class VotacaoNominalExpedienteView(VotacaoNominalAbstract):
    expediente = True
    ordem = False


class VotacaoNominalEditView(VotacaoNominalEditAbstract):
    ordem = True
    expediente = False


class VotacaoNominalExpedienteEditView(VotacaoNominalEditAbstract):
    expediente = True
    ordem = False


class VotacaoNominalTransparenciaDetailView(TemplateView):
    template_name = 'sessao/votacao/nominal_transparencia.html'

    def get_context_data(self, **kwargs):
        context = super(VotacaoNominalTransparenciaDetailView,
                        self).get_context_data(**kwargs)

        materia_votacao = self.request.GET.get('materia', None)

        if materia_votacao == 'ordem':
            votacao = RegistroVotacao.objects.get(ordem=self.kwargs['oid'])
        elif materia_votacao == 'expediente':
            votacao = RegistroVotacao.objects.get(expediente=self.kwargs['oid'])
        else:
            raise Http404()

        context['votacao'] = votacao

        voto_parlamentar = VotoParlamentar.objects.filter(
            votacao=votacao)

        context['voto_parlamentar'] = voto_parlamentar

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'resultado': votacao.tipo_resultado_votacao.nome,
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'resultado_votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return context

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo


class VotacaoNominalExpedienteDetailView(DetailView):
    template_name = 'sessao/votacao/nominal_detail.html'

    def get(self, request, *args, **kwargs):
        context = {}
        materia_id = kwargs['mid']
        expediente_id = kwargs['oid']

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
                       '&nbsp;', ' ', strip_tags(expediente.materia.ementa))}
        context.update({'materia': materia})

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'resultado': votacao.tipo_resultado_votacao.nome,
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao': votacao_existente,
                        'tipos': self.get_tipos_votacao()})

        return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sapl.sessao:expedientemateria_list',
                       kwargs={'pk': pk})


class VotacaoExpedienteView(SessaoPermissionMixin):

    """
        Votação Simbólica e Secreta
    """

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

        expediente_id = kwargs['oid']
        expediente = ExpedienteMateria.objects.get(id=expediente_id)
        qtde_presentes = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': expediente.materia,
                   'ementa': expediente.materia.ementa}
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

        expediente_id = kwargs['oid']
        expediente = ExpedienteMateria.objects.get(id=expediente_id)
        qtde_presentes = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': expediente.materia,
                   'ementa': expediente.materia.ementa}
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
            materia_id = kwargs['mid']
            expediente_id = kwargs['oid']

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

    """
        Votação Simbólica e Secreta
    """

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

        materia_id = kwargs['mid']
        expediente_id = kwargs['oid']

        expediente = ExpedienteMateria.objects.get(id=expediente_id)

        materia = {'materia': expediente.materia,
                   'ementa': expediente.materia.ementa}
        context.update({'materia': materia})

        try:
            votacao = RegistroVotacao.objects.get(
                materia_id=materia_id,
                expediente_id=expediente_id)
        except MultipleObjectsReturned:
            votacao = RegistroVotacao.objects.filter(
                materia_id=materia_id,
                expediente_id=expediente_id).last()
        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'resultado': votacao.tipo_resultado_votacao.nome,
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao_titulo': titulo,
                        'votacao': votacao_existente})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = VotacaoEditForm(request.POST)

        materia_id = kwargs['mid']
        expediente_id = kwargs['oid']

        if(int(request.POST['anular_votacao']) == 1):
            for r in RegistroVotacao.objects.filter(
                    expediente_id=expediente_id):
                r.delete()

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
            ementa = m.materia.ementa
            titulo = m.materia
            numero = m.numero_ordem

            ultima_tramitacao = m.materia.tramitacao_set.last()

            situacao = ultima_tramitacao.status if ultima_tramitacao else None

            if situacao is None:
                situacao = _("Não informada")
            rv = m.registrovotacao_set.all()
            if rv:
                resultado = rv[0].tipo_resultado_votacao.nome
                resultado_observacao = rv[0].observacao
            else:
                resultado = _('Matéria não votada')
                resultado_observacao = _(' ')

            autoria = Autoria.objects.filter(materia_id=m.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'id': m.materia_id,
                   'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'resultado_observacao': resultado_observacao,
                   'situacao': situacao,
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
                '&nbsp;', ' ', strip_tags(e.conteudo.replace('<br/>', '\n')))

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
            ementa = o.materia.ementa
            titulo = o.materia
            numero = o.numero_ordem

            ultima_tramitacao = o.materia.tramitacao_set.last()

            situacao = ultima_tramitacao.status if ultima_tramitacao else None

            if situacao is None:
                situacao = _("Não informada")
            # Verificar resultado
            rv = o.registrovotacao_set.all()
            if rv:
                resultado = rv[0].tipo_resultado_votacao.nome
                resultado_observacao = rv[0].observacao
            else:
                resultado = _('Matéria não votada')
                resultado_observacao = _(' ')

            autoria = Autoria.objects.filter(
                materia_id=o.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'id': o.materia_id,
                   'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'resultado_observacao': resultado_observacao,
                   'situacao': situacao,
                   'autor': autor
                   }
            materias_ordem.append(mat)

        context.update({'materias_ordem': materias_ordem})
        context.update({'subnav_template_name': 'sessao/pauta_subnav.yaml'})

        return self.render_to_response(context)


class PesquisarSessaoPlenariaView(FilterView):
    model = SessaoPlenaria
    filterset_class = SessaoPlenariaFilterSet
    paginate_by = 10

    def get_filterset_kwargs(self, filterset_class):
        super(PesquisarSessaoPlenariaView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset().select_related(
            'tipo', 'sessao_legislativa', 'legislatura')

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
        if data and data.get('data_inicio__year') is not None:
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

        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        return self.render_to_response(context)


class PesquisarPautaSessaoView(PesquisarSessaoPlenariaView):
    filterset_class = PautaSessaoFilterSet
    template_name = 'sessao/pauta_sessao_filter.html'

    def get_context_data(self, **kwargs):
        context = super(PesquisarPautaSessaoView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Pesquisar Pauta de Sessão')
        return context


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

        if 'tramitacao__status' in self.request.GET:
            if self.request.GET['tramitacao__status']:
                lista_status = filtra_tramitacao_status(
                    self.request.GET['tramitacao__status'])

                lista_materias_adicionadas = retira_materias_ja_adicionadas(
                    self.kwargs['pk'], ExpedienteMateria)

                qs = qs.filter(id__in=lista_status).exclude(
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
                # TODO: o campo observacao deve ser uma copia de ML.ementa?
                expediente.observacao = MateriaLegislativa.objects.get(
                    pk=materia.id).ementa
                if lista_materias_expediente:
                    posicao = lista_materias_expediente.last().numero_ordem + 1
                    expediente.numero_ordem = posicao
                else:
                    expediente.numero_ordem = 1
                expediente.data_ordem = timezone.now()
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

        if 'tramitacao__status' in self.request.GET:
            if self.request.GET['tramitacao__status']:
                lista_status = filtra_tramitacao_status(
                    self.request.GET['tramitacao__status'])

                lista_materias_adicionadas = retira_materias_ja_adicionadas(
                    self.kwargs['pk'], OrdemDia)

                qs = qs.filter(id__in=lista_status).exclude(
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
                # TODO: o campo observacao deve ser uma copia de ML.ementa?
                ordem_dia.observacao = MateriaLegislativa.objects.get(
                    pk=materia.id).ementa
                if lista_materias_ordem_dia:
                    posicao = lista_materias_ordem_dia.last().numero_ordem + 1
                    ordem_dia.numero_ordem = posicao
                else:
                    ordem_dia.numero_ordem = 1
                ordem_dia.data_ordem = timezone.now()
                ordem_dia.tipo_votacao = tipo_votacao
                ordem_dia.save()

        return self.get(request, self.kwargs)


@csrf_exempt
@permission_required('sessao.change_expedientemateria',
                     'sessao.change_ordemdia')
def mudar_ordem_materia_sessao(request):
    # Pega os dados vindos da requisição
    posicao_inicial = int(request.POST['pos_ini']) + 1
    posicao_final = int(request.POST['pos_fim']) + 1
    pk_sessao = int(request.POST['pk_sessao'])

    materia = request.POST['materia']

    # Verifica se está nas Matérias do Expediente ou da Ordem do Dia
    if materia == 'expediente':
        materia = ExpedienteMateria
    elif materia == 'ordem':
        materia = OrdemDia
    else:
        return

    # Testa se existe alguma matéria na posição recebida
    try:
        materia_1 = materia.objects.get(
            sessao_plenaria=pk_sessao,
            numero_ordem=posicao_inicial)
    except ObjectDoesNotExist:
        raise  # TODO tratar essa exceção

    # Se a posição inicial for menor que a final, todos que
    # estiverem acima da nova posição devem ter sua ordem decrementada
    # em uma posição
    if posicao_inicial < posicao_final:
        materias_expediente = materia.objects.filter(
            sessao_plenaria=pk_sessao,
            numero_ordem__lte=posicao_final,
            numero_ordem__gte=posicao_inicial)
        for m in materias_expediente:
            m.numero_ordem = m.numero_ordem - 1
            m.save()

    # Se a posição inicial for maior que a final, todos que
    # estiverem abaixo da nova posição devem ter sua ordem incrementada
    # em uma posição
    elif posicao_inicial > posicao_final:
        materias_expediente = materia.objects.filter(
            sessao_plenaria=pk_sessao,
            numero_ordem__gte=posicao_final,
            numero_ordem__lte=posicao_inicial)
        for m in materias_expediente:
            m.numero_ordem = m.numero_ordem + 1
            m.save()

    materia_1.numero_ordem = posicao_final
    materia_1.save()

    return
