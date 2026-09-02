from datetime import datetime
import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import F, Q
from django.db.models.aggregates import Count
from django.http import Http404, JsonResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import FormView
from django.views.generic.edit import UpdateView
from django_filters.views import FilterView
from image_cropping.utils import get_backend

from sapl.base.forms import SessaoLegislativaForm, PartidoForm
from sapl.base.models import Autor
from sapl.comissoes.models import Participacao
from sapl.crud.base import (RP_CHANGE, RP_DETAIL, RP_LIST, Crud, CrudAux,
                            CrudBaseForListAndDetailExternalAppView,
                            MasterDetailCrud, make_pagination)
from sapl.materia.models import Autoria, Proposicao, Relatoria
from sapl.norma.models import AutoriaNorma, NormaJuridica
from sapl.parlamentares.apps import AppConfig
from sapl.rules import SAPL_GROUP_VOTANTE
from sapl.utils import (parlamentares_ativos, show_results_filter_set, ratelimit_ip)

from .forms import (ColigacaoFilterSet, ComposicaoMesaForm, FiliacaoForm, FrenteForm, LegislaturaForm, MandatoForm, MesaDiretoraFilterSet, MesaDiretoraForm,
                    ParlamentarCreateForm, ParlamentarForm, VotanteForm,
                    ParlamentarFilterSet, PartidoFilterSet, VincularParlamentarForm,
                    BlocoForm, FrenteParlamentarForm, BlocoMembroForm)
from .models import (CargoMesa, Coligacao, ComposicaoColigacao, ComposicaoMesa,
                     Dependente, Filiacao, Frente, Legislatura, Mandato,
                     NivelInstrucao, Parlamentar, Partido, SessaoLegislativa,
                     SituacaoMilitar, TipoAfastamento, TipoDependente, Votante,
                     Bloco, FrenteCargo, FrenteParlamentar, BlocoCargo, BlocoMembro, MesaDiretora)

from ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from ..settings import RATE_LIMITER_RATE

FrenteCargoCrud = CrudAux.build(FrenteCargo, 'frente_cargo')
BlocoCargoCrud = CrudAux.build(BlocoCargo, 'bloco_cargo')
CargoMesaCrud = CrudAux.build(CargoMesa, 'cargo_mesa')
TipoDependenteCrud = CrudAux.build(TipoDependente, 'tipo_dependente')
NivelInstrucaoCrud = CrudAux.build(NivelInstrucao, 'nivel_instrucao')
TipoAfastamentoCrud = CrudAux.build(TipoAfastamento, 'tipo_afastamento')
TipoMilitarCrud = CrudAux.build(SituacaoMilitar, 'tipo_situa_militar')

DependenteCrud = MasterDetailCrud.build(
    Dependente, 'parlamentar', 'dependente')


class SessaoLegislativaCrud(CrudAux):
    model = SessaoLegislativa

    class CreateView(CrudAux.CreateView):
        form_class = SessaoLegislativaForm

    class UpdateView(CrudAux.UpdateView):
        form_class = SessaoLegislativaForm


class PartidoCrud(CrudAux):
    model = Partido

    class CreateView(CrudAux.CreateView):
        form_class = PartidoForm

    class UpdateView(CrudAux.UpdateView):
        form_class = PartidoForm

    class DeleteView(CrudAux.DeleteView):
        def get_success_url(self):
            return reverse('sapl.parlamentares:pesquisar_partido')


class VotanteView(MasterDetailCrud):
    model = Votante
    parent_field = 'parlamentar'
    UpdateView = None

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['user']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = VotanteForm
        layout_key = None

    class DetailView(MasterDetailCrud.DetailView):

        def detail_create_url(self):
            return None

    class DeleteView(MasterDetailCrud.DeleteView):

        def delete(self, *args, **kwargs):
            obj = self.get_object()

            g = Group.objects.filter(name=SAPL_GROUP_VOTANTE)[0]
            obj.user.groups.remove(g)

            obj.delete()
            return HttpResponseRedirect(
                reverse('sapl.parlamentares:votante_list',
                        kwargs={'pk': obj.parlamentar.pk}))


class FrenteList(MasterDetailCrud):
    public = [RP_DETAIL, RP_LIST]
    model = Frente
    is_m2m = True
    parent_field = 'parlamentares'
    CreateView, UpdateView, DeleteView = None, None, None

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['nome', 'data_criacao', 'data_extincao']

        @classmethod
        def url_name(cls, suffix):
            return '%s_parlamentar_%s' % (cls.model._meta.model_name, suffix)


class RelatoriaParlamentarCrud(CrudBaseForListAndDetailExternalAppView):
    public = [RP_DETAIL, RP_LIST]
    model = Relatoria
    parent_field = 'parlamentar'
    help_topic = 'tramitacao_relatoria'
    namespace = AppConfig.name

    class BaseMixin(CrudBaseForListAndDetailExternalAppView.BaseMixin):

        @classmethod
        def url_name(cls, suffix):
            return '%s_parlamentar_%s' % (cls.model._meta.model_name, suffix)


class ProposicaoParlamentarCrud(CrudBaseForListAndDetailExternalAppView):
    model = Proposicao
    list_field_names = ['tipo', 'descricao']
    parent_field = 'autor__parlamentar_set'
    namespace = AppConfig.name

    class BaseMixin(CrudBaseForListAndDetailExternalAppView.BaseMixin):

        @classmethod
        def url_name(cls, suffix):
            return '%s_parlamentar_%s' % (cls.model._meta.model_name, suffix)

    class ListView(CrudBaseForListAndDetailExternalAppView.ListView):

        def get_context_data(self, **kwargs):
            context = CrudBaseForListAndDetailExternalAppView \
                .ListView.get_context_data(self, **kwargs)
            return context

        def get_queryset(self):
            return super().get_queryset().filter(
                data_envio__isnull=False,
                data_recebimento__isnull=False,
                cancelado=False)

    class DetailView(CrudBaseForListAndDetailExternalAppView.DetailView):

        def get_queryset(self):
            return super().get_queryset().filter(
                cancelado=False)

        @property
        def extras_url(self):
            if self.object.texto_articulado.exists():
                ta = self.object.texto_articulado.first()
                yield (str(reverse_lazy(
                    'sapl.compilacao:ta_text',
                    kwargs={'ta_id': ta.pk})) + '?back_type=history',
                    'btn-success',
                    _('Texto Eletrônico'))


@method_decorator(ratelimit(key=ratelimit_ip,
                            rate=RATE_LIMITER_RATE,
                            block=True),
                  name='dispatch')
class PesquisarParlamentarView(FilterView):
    model = Parlamentar
    filterset_class = ParlamentarFilterSet
    paginate_by = 20

    def get_filterset_kwargs(self, filterset_class):
        super(PesquisarParlamentarView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset().order_by('nome_parlamentar').distinct()

        kwargs.update({
            'queryset': qs,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(PesquisarParlamentarView,
                        self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        context['NO_ENTRIES_MSG'] = 'Nenhum parlamentar encontrado!'

        context['title'] = _('Parlamentares')

        return context

    def get(self, request, *args, **kwargs):
        super(PesquisarParlamentarView, self).get(request)

        data = self.filterset.data
        url = ''
        if data:
            url = "&" + str(self.request.META['QUERY_STRING'])
            if url.startswith("&page"):
                url = ''

        if 'nome_parlamentar' in self.request.META['QUERY_STRING'] or\
                'page' in self.request.META['QUERY_STRING']:
            resultados = self.object_list
        else:
            resultados = []

        context = self.get_context_data(filter=self.filterset,
                                        object_list=resultados,
                                        filter_url=url,
                                        numero_res=len(resultados)
                                        )

        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        return self.render_to_response(context)


@method_decorator(ratelimit(key=ratelimit_ip,
                            rate=RATE_LIMITER_RATE,
                            block=True),
                  name='dispatch')
class PesquisarColigacaoView(FilterView):
    model = Coligacao
    filterset_class = ColigacaoFilterSet
    paginate_by = 20

    def get_filterset_kwargs(self, filterset_class):
        super(PesquisarColigacaoView, self).get_filterset_kwargs(filterset_class)

        return ({
            'data': self.request.GET or None,
            'queryset': self.get_queryset().order_by('nome').distinct()
        })

    def get_context_data(self, **kwargs):
        context = super(PesquisarColigacaoView,
                        self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context.update({
            'page_range': make_pagination(page_obj.number, paginator.num_pages),
            'NO_ENTRIES_MSG': 'Nenhuma coligação encontrada!',
            'title': _('Coligações')
        })

        return context

    def get(self, request, *args, **kwargs):
        super(PesquisarColigacaoView, self).get(request)

        data = self.filterset.data
        url = ''
        if data:
            url = "&" + str(self.request.META['QUERY_STRING'])
            if url.startswith("&page"):
                url = ''

        if 'nome' in self.request.META['QUERY_STRING'] or\
                'page' in self.request.META['QUERY_STRING']:
            resultados = self.object_list
        else:
            resultados = []

        context = self.get_context_data(filter=self.filterset,
                                        object_list=resultados,
                                        filter_url=url,
                                        numero_res=len(resultados)
                                        )

        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        return self.render_to_response(context)


@method_decorator(ratelimit(key=ratelimit_ip,
                            rate=RATE_LIMITER_RATE,
                            block=True),
                  name='dispatch')
class PesquisarPartidoView(FilterView):
    model = Partido
    filterset_class = PartidoFilterSet
    paginate_by = 20

    def get_filterset_kwargs(self, filterset_class):
        super(PesquisarPartidoView, self).get_filterset_kwargs(filterset_class)

        return ({
            'data': self.request.GET or None,
            'queryset': self.get_queryset().order_by('nome').distinct()
        })

    def get_context_data(self, **kwargs):
        context = super(PesquisarPartidoView, self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context.update({
            'page_range': make_pagination(page_obj.number, paginator.num_pages),
            'NO_ENTRIES_MSG': 'Nenhum partido encontrado!',
            'title': _('Partidos')
        })

        return context

    def get(self, request, *args, **kwargs):
        super(PesquisarPartidoView, self).get(request)

        data = self.filterset.data
        url = ''
        if data:
            url = "&" + str(self.request.META['QUERY_STRING'])
            if url.startswith("&page"):
                url = ''

        if 'nome' in self.request.META['QUERY_STRING'] or\
                'page' in self.request.META['QUERY_STRING']:
            resultados = self.object_list
        else:
            resultados = []

        context = self.get_context_data(filter=self.filterset,
                                        object_list=resultados,
                                        filter_url=url,
                                        numero_res=len(resultados)
                                        )

        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        return self.render_to_response(context)


class ParticipacaoParlamentarCrud(CrudBaseForListAndDetailExternalAppView):
    public = [RP_DETAIL, RP_LIST]
    model = Participacao
    parent_field = 'parlamentar'
    namespace = AppConfig.name
    list_field_names = ['composicao__comissao__nome', 'cargo__nome', (
        'composicao__periodo__data_inicio', 'composicao__periodo__data_fim')]

    class BaseMixin(CrudBaseForListAndDetailExternalAppView.BaseMixin):

        @classmethod
        def url_name(cls, suffix):
            return '%s_parlamentar_%s' % (cls.model._meta.model_name, suffix)

    class ListView(CrudBaseForListAndDetailExternalAppView.ListView):
        ordering = ('-composicao__periodo')

        def get_rows(self, object_list):
            """
            FIXME:
                Este metodo não será necessário quando get_rows for refatorada
            """

            comissoes = []
            for p in object_list:
                # TODO: atualmente periodo.data_fim pode ser nulo o que pode
                # gerar um erro nessa tela
                data_fim = p.composicao.periodo.data_fim
                if data_fim:
                    data_fim = data_fim.strftime("%d/%m/%Y")
                else:
                    data_fim = ' - '

                comissao = [
                    (p.composicao.comissao.nome, reverse(
                        'sapl.comissoes:comissao_detail', kwargs={
                            'pk': p.composicao.comissao.pk})),
                    (p.cargo.nome, None),
                    (p.composicao.periodo.data_inicio.strftime(
                        "%d/%m/%Y") + ' a ' +
                     data_fim,
                     None)
                ]
                comissoes.append(comissao)
            return comissoes

        def get_headers(self):
            return [_('Comissão'), _('Cargo'), _('Período de participação'), ]


class ColigacaoCrud(CrudAux):
    model = Coligacao
    help_topic = 'coligacao'

    class ListView(CrudAux.ListView):
        ordering = ('legislatura', '-nome')

        def get_context_data(self, **kwargs):
            context = super(ColigacaoCrud.ListView, self).get_context_data(
                kwargs=kwargs)
            rows = context['rows']
            coluna_votos_recebidos = 2
            for row in rows:
                if not row[coluna_votos_recebidos][0]:
                    row[coluna_votos_recebidos] = ('0', None)

            return context

    class DetailView(CrudAux.DetailView):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(kwargs=kwargs)
            coligacao = context['coligacao']
            if not coligacao.numero_votos:
                coligacao.numero_votos = '0'

            context['subnav_template_name'] = 'parlamentares/subnav_coligacao.yaml'

            return context

    class UpdateView(CrudAux.UpdateView):

        def get_context_data(self, **kwargs):
            context = super(UpdateView, self).get_context_data(kwargs=kwargs)
            context['subnav_template_name'] = 'parlamentares/subnav_coligacao.yaml'

            return context

    class DeleteView(CrudAux.DeleteView):
        def get_success_url(self):
            return reverse('sapl.parlamentares:pesquisar_coligacao')


def coligacao_legislatura(request):
    try:
        coligacoes = Coligacao.objects.filter(
            legislatura=request.GET['legislatura']).order_by('nome')
    except:
        coligacoes = []

    lista_coligacoes = [(coligacao.id, str(coligacao))
                        for coligacao in coligacoes]

    return JsonResponse({'coligacoes': lista_coligacoes})


def json_date_convert(date):
    """
    :param date: recebe a data de uma chamada ajax no formato de
     string "dd/mm/yyyy"
    :return:
    """

    return datetime.strptime(date, "%d/%m/%Y").date()


def frente_atualiza_lista_parlamentares(request):
    """
    :param request: recebe os parâmetros do GET da chamada Ajax
    :return: retorna a lista atualizada dos parlamentares
    """
    ativos = json.loads(request.GET['ativos'])

    parlamentares = Parlamentar.objects.all()

    if ativos:
        if 'data_criacao' in request.GET and request.GET['data_criacao']:
            data_criacao = json_date_convert(request.GET['data_criacao'])

            if 'data_extincao' in request.GET and request.GET['data_extincao']:
                data_extincao = json_date_convert(request.GET['data_extincao'])
                parlamentares = parlamentares_ativos(data_criacao,
                                                     data_extincao)
            else:
                parlamentares = parlamentares_ativos(data_criacao)

    parlamentares_list = [(p.id, p.__str__()) for p in parlamentares]

    return JsonResponse({'parlamentares_list': parlamentares_list})


def parlamentares_frente_selected(request):
    """
    :return: Lista com o id dos parlamentares em uma frente
    """
    logger = logging.getLogger(__name__)
    username = request.user.username
    try:
        logger.info("user=" + username +
                    ". Tentando objet objeto Frente com id={}.".format(request.GET['frente_id']))
        frente = Frente.objects.get(id=int(request.GET['frente_id']))
    except ObjectDoesNotExist:
        logger.error("user=" + username +
                     ". Frente buscada (id={}) não existe. Retornada lista vazia.".format(request.GET['frente_id']))
        lista_parlamentar_id = []
    else:
        logger.info("user=" + username +
                    ". Frente (id={}) encontrada com sucesso.".format(request.GET['frente_id']))
        lista_parlamentar_id = frente.parlamentares.all().values_list(
            'id', flat=True)
    return JsonResponse({'id_list': list(lista_parlamentar_id)})


class FrenteCrud(Crud):
    model = Frente
    help_topic = 'tipo_situa_militar'
    public = [RP_DETAIL, RP_LIST]
    list_field_names = ['nome', 'data_criacao', 'data_extincao']

    class BaseMixin(Crud.BaseMixin):
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

    class CreateView(Crud.CreateView):
        form_class = FrenteForm

        def form_valid(self, form):
            return super(Crud.CreateView, self).form_valid(form)

    class UpdateView(Crud.UpdateView):
        form_class = FrenteForm


class FrenteParlamentarCrud(MasterDetailCrud):
    model = FrenteParlamentar
    parent_field = 'frente'
    help_topic = 'frente_parlamentares'
    public = [RP_LIST, RP_DETAIL]

    class CreateView(MasterDetailCrud.CreateView):
        form_class = FrenteParlamentarForm

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

        def get_initial(self):
            self.initial['frente'] = Frente.objects.get(pk=self.kwargs['pk'])
            return self.initial

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = FrenteParlamentarForm

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

    class DetailView(MasterDetailCrud.DetailView):
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

    class ListView(MasterDetailCrud.ListView):
        layout_key = 'FrenteParlamentarList'
        ordering = ('-cargo__cargo_unico', 'parlamentar')

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context


def get_parlamentar_frentes(request, pk):
    template_name = 'parlamentares/parlamentar_frentes_list.html'
    frentes = [f for f in FrenteParlamentar.objects.filter(parlamentar_id=pk)
               .select_related('frente', 'cargo')
               .order_by('-data_entrada', '-data_saida')]

    context = {
        'subnav_template_name': 'parlamentares/subnav.yaml',
        'root_pk': pk,
        'sexo_parlamentar': Parlamentar.objects.get(id=pk).sexo,
        'nome_parlamentar': Parlamentar.objects.get(id=pk).nome_parlamentar,
        'frentes': frentes,
        'num_frentes': len(frentes)
    }

    return render(request, template_name, context)


class MandatoCrud(MasterDetailCrud):
    model = Mandato
    parent_field = 'parlamentar'
    public = [RP_DETAIL, RP_LIST]
    list_field_names = ['legislatura',
                        'votos_recebidos',
                        'coligacao',
                        'coligacao__numero_votos',
                        'titular']

    class ListView(MasterDetailCrud.ListView):
        ordering = ('-legislatura__numero')

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            rows = context['rows']

            coluna_coligacao = 2
            coluna_votos_recebidos = 3
            for row in rows:
                if not row[coluna_coligacao][0]:
                    row[coluna_coligacao] = (' ', None)

                if not row[coluna_votos_recebidos][0]:
                    row[coluna_votos_recebidos] = (' ', None)

            return context

    class CreateView(MasterDetailCrud.CreateView):
        form_class = MandatoForm

        def get_initial(self):
            return {'parlamentar': Parlamentar.objects.get(
                pk=self.kwargs['pk'])}

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = MandatoForm


class ComposicaoColigacaoCrud(MasterDetailCrud):
    model = ComposicaoColigacao
    parent_field = 'coligacao'
    help_topic = 'coligacao'

    class BaseMixin(MasterDetailCrud.BaseMixin):

        def get_context_data(self, **kwargs):
            context = super().get_context_data()
            context['subnav_template_name'] = \
                'parlamentares/subnav_coligacao.yaml'
            return context

    class ListView(MasterDetailCrud.ListView):
        ordering = '-partido__sigla'


class LegislaturaCrud(CrudAux):
    model = Legislatura
    help_topic = 'legislatura'
    list_field_names = [
        'numero',
        'data_eleicao',
        'data_inicio',
        'data_fim']

    class CreateView(CrudAux.CreateView):
        logger = logging.getLogger(__name__)
        form_class = LegislaturaForm

        def get_initial(self):
            username = self.request.user.username
            try:
                self.logger.error("user=" + username +
                                  ". Tentando obter última Legislatura.")
                ultima_legislatura = Legislatura.objects.latest('numero')
                numero = ultima_legislatura.numero + 1
            except Legislatura.DoesNotExist:
                self.logger.error(
                    "user=" + username + ". Legislatura não encontrada. Número definido como 1.")
                numero = 1
            return {'numero': numero}

    class UpdateView(CrudAux.UpdateView):
        form_class = LegislaturaForm

    class DetailView(CrudAux.DetailView):

        def has_permission(self):
            return True

        @xframe_options_exempt
        def get(self, request, *args, **kwargs):
            return super().get(request, *args, **kwargs)

    class ListView(CrudAux.ListView):

        def has_permission(self):
            return True

        @xframe_options_exempt
        def get(self, request, *args, **kwargs):
            return super().get(request, *args, **kwargs)


class FiliacaoCrud(MasterDetailCrud):
    model = Filiacao
    parent_field = 'parlamentar'
    help_topic = 'filiacoes_partidarias'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        ordering = '-data'

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = FiliacaoForm

    class CreateView(MasterDetailCrud.CreateView):
        form_class = FiliacaoForm


class ParlamentarCrud(Crud):
    model = Parlamentar
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(Crud.BaseMixin):
        ordered_list = False
        list_field_names = [
            'nome_parlamentar',
            'sigla_partido_filiacao_atual',
            'ativo']

    class DetailView(Crud.DetailView):

        def get_template_names(self):
            if self.request.user.has_perm(self.permission(RP_CHANGE)):
                if 'iframe' not in self.request.GET:
                    if not self.request.session.get('iframe'):
                        return ['crud/detail.html']
                elif self.request.GET['iframe'] == '0':
                    return ['crud/detail.html']

            return ['parlamentares/parlamentar_perfil_publico.html']

        @xframe_options_exempt
        def get(self, request, *args, **kwargs):
            return super().get(request, *args, **kwargs)

    class UpdateView(Crud.UpdateView):
        form_class = ParlamentarForm

        layout_key = 'ParlamentarUpdate'

        def render_to_response(self, context, **response_kwargs):
            context['form'].helper.include_media = False
            return super().render_to_response(context, **response_kwargs)

    class CreateView(Crud.CreateView):
        form_class = ParlamentarCreateForm

        layout_key = 'ParlamentarCreate'

        def form_valid(self, form):
            """
            Reimplementa form_valid devido ao save de ParlamentarCreateForm
            ser específico, sendo necessário isolar padrão do crud que aciona
            form.save(commit=False) para registrar dados de auditoria se
            o model implementá-los, bem como de container se também implement.
            """
            return super(Crud.CreateView, self).form_valid(form)

    class ListView(Crud.ListView):
        template_name = "parlamentares/parlamentares_list.html"
        paginate_by = None
        logger = logging.getLogger(__name__)

        @xframe_options_exempt
        def get(self, request, *args, **kwargs):
            return super().get(request, *args, **kwargs)

        def take_legislatura_id(self):
            username = self.request.user.username
            try:
                self.logger.debug("user=" + username +
                                  ". Tentando obter id da legislatura.")
                return int(self.request.GET['pk'])
            except:
                self.logger.warning(
                    "User=" + username + ". Legislatura não possui ID. Buscando em todas as entradas.")
                legislaturas = Legislatura.objects.all()
                for l in legislaturas:
                    if l.atual():
                        return l.id
                if legislaturas:
                    return legislaturas[0].id
                return -1

        def get_queryset(self):
            self.logger = logging.getLogger(__name__)
            queryset = super().get_queryset()
            legislatura_id = self.take_legislatura_id()
            # Pelo menos uma casa legislativa criou uma
            # legislatura de numero zero, o que é um absurdo
            username = self.request.user.username
            if legislatura_id >= 0:
                return queryset.filter(
                    mandato__legislatura_id=legislatura_id).distinct()
            else:
                try:
                    self.logger.debug(
                        "user=" + username + ". Tentando obter o mais recente registro do objeto Legislatura.")
                    l = Legislatura.objects.all().order_by(
                        '-data_inicio').first()
                except ObjectDoesNotExist:
                    self.logger.error(
                        "user=" + username + ". Objeto não encontrado. Retornando todos os registros.")
                    return Legislatura.objects.all()
                else:
                    self.logger.info("user=" + username +
                                     ". Objeto encontrado com sucesso.")
                    if l is None:
                        return Legislatura.objects.all()
                    return queryset.filter(mandato__legislatura_id=l)

        def get_headers(self):
            return [_('Parlamentar'), _('Partido'),
                    _('Ativo?'), _('Titular?')]


class ParlamentarMateriasView(FormView):
    template_name = "parlamentares/materias.html"
    success_url = reverse_lazy('sapl.parlamentares:parlamentar_materia')
    logger = logging.getLogger(__name__)

    def get_autoria(self, resultset):
        autoria = {}
        total_autoria = 0

        for i in resultset:
            row = autoria.get(i['materia__ano'], [])
            columns = (i['materia__tipo__pk'],
                       i['materia__tipo__sigla'],
                       i['materia__tipo__descricao'],
                       int(i['total']))
            row.append(columns)
            autoria[i['materia__ano']] = row
            total_autoria += columns[3]
        autoria = sorted(autoria.items(), reverse=True)
        return autoria, total_autoria

    @xframe_options_exempt
    def get(self, request, *args, **kwargs):
        parlamentar_pk = kwargs['pk']
        username = request.user.username
        try:
            self.logger.debug(
                "user=" + username + ". Tentando obter Autor (object_id={}).".format(parlamentar_pk))
            autor = Autor.objects.get(
                content_type=ContentType.objects.get_for_model(Parlamentar),
                object_id=parlamentar_pk)
        except ObjectDoesNotExist:
            mensagem = _(
                'Este Parlamentar não está associado como autor de matéria.'.format(parlamentar_pk))
            self.logger.error(
                "user=" + username + ". Este Parlamentar (pk={}) não é Autor de matéria.".format(parlamentar_pk))
            messages.add_message(request, messages.ERROR, mensagem)
            return HttpResponseRedirect(
                reverse(
                    'sapl.parlamentares:parlamentar_detail',
                    kwargs={'pk': parlamentar_pk}))

        autoria = Autoria.objects.filter(
            autor=autor, primeiro_autor=True).values(
            'materia__ano',
            'materia__tipo__pk',
            'materia__tipo__sigla',
            'materia__tipo__descricao').annotate(
            total=Count('materia__tipo__pk')).order_by(
            '-materia__ano', 'materia__tipo')

        coautoria = Autoria.objects.filter(
            autor=autor, primeiro_autor=False).values(
            'materia__ano',
            'materia__tipo__pk',
            'materia__tipo__sigla',
            'materia__tipo__descricao').annotate(
            total=Count('materia__tipo__pk')).order_by(
            '-materia__ano', 'materia__tipo')

        autor_list = self.get_autoria(autoria)
        coautor_list = self.get_autoria(coautoria)

        parlamentar_pk = autor.autor_related.pk
        nome_parlamentar = autor.autor_related.nome_parlamentar

        return self.render_to_response({'autor_pk': autor.pk,
                                        'root_pk': parlamentar_pk,
                                        'autoria': autor_list,
                                        'coautoria': coautor_list,
                                        'nome_parlamentar': nome_parlamentar
                                        })


class ParlamentarNormasView(FormView):
    template_name = "norma/normas.html"
    success_url = reverse_lazy('sapl.parlamentares:parlamentar_normas')
    logger = logging.getLogger(__name__)

    def get_autoria(self, resultset):
        autoria = {}
        total_autoria = 0

        for i in resultset:
            row = autoria.get(i['norma__ano'], [])
            columns = (i['norma__tipo__pk'],
                       i['norma__tipo__sigla'],
                       i['norma__tipo__descricao'],
                       int(i['total']))
            row.append(columns)
            autoria[i['norma__ano']] = row
            total_autoria += columns[3]
        autoria = sorted(autoria.items(), reverse=True)
        return autoria, total_autoria

    @xframe_options_exempt
    def get(self, request, *args, **kwargs):
        parlamentar_pk = kwargs['pk']
        username = request.user.username
        try:
            self.logger.debug(
                "user=" + username + ". Tentando obter Autor (object_id={}).".format(parlamentar_pk))
            autor = Autor.objects.get(
                content_type=ContentType.objects.get_for_model(Parlamentar),
                object_id=parlamentar_pk)
        except ObjectDoesNotExist:
            mensagem = _(
                'Este Parlamentar não está associado como autor de matéria.'.format(parlamentar_pk))
            self.logger.error(
                "user=" + username + ". Este Parlamentar (pk={}) não é Autor de matéria.".format(parlamentar_pk))
            messages.add_message(request, messages.ERROR, mensagem)
            return HttpResponseRedirect(
                reverse(
                    'sapl.parlamentares:parlamentar_detail',
                    kwargs={'pk': parlamentar_pk}))

        autoria = AutoriaNorma.objects.filter(
            autor=autor, primeiro_autor=True).values(
            'norma__ano',
            'norma__tipo__pk',
            'norma__tipo__sigla',
            'norma__tipo__descricao').annotate(
            total=Count('norma__tipo__pk')).order_by(
            '-norma__ano', 'norma__tipo')

        coautoria = AutoriaNorma.objects.filter(
            autor=autor, primeiro_autor=False).values(
            'norma__ano',
            'norma__tipo__pk',
            'norma__tipo__sigla',
            'norma__tipo__descricao').annotate(
            total=Count('norma__tipo__pk')).order_by(
            '-norma__ano', 'norma__tipo')

        autor_list = self.get_autoria(autoria)
        coautor_list = self.get_autoria(coautoria)

        parlamentar_pk = autor.autor_related.pk
        nome_parlamentar = autor.autor_related.nome_parlamentar

        return self.render_to_response({'autor_pk': autor.pk,
                                        'root_pk': parlamentar_pk,
                                        'autoria': autor_list,
                                        'coautoria': coautor_list,
                                        'nome_parlamentar': nome_parlamentar
                                        })


def get_data_filicao(parlamentar):
    return parlamentar.filiacao_set.order_by('-data').first().data.strftime('%d/%m/%Y')


def parlamentares_filiados(request, pk):
    template_name = 'parlamentares/partido_filiados.html'
    parlamentares = Parlamentar.objects.all()
    partido = Partido.objects.get(pk=pk)
    parlamentares_filiados = [(parlamentar, get_data_filicao(parlamentar)) for parlamentar in parlamentares if
                              parlamentar.sigla_partido_filiacao_atual == partido.sigla]
    return render(request, template_name, {'partido': partido, 'parlamentares': parlamentares_filiados})


class MesaDiretoraCrud(Crud):
    model = MesaDiretora
    help_topic = 'mesa_diretora'
    public = [RP_DETAIL, RP_LIST]

    class BaseMixin(Crud.BaseMixin):
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            if 'subnav_template_name' not in context:
                context['subnav_template_name'] = 'parlamentares/subnav_mesa.yaml'
            return context

    class ListView(FilterView, Crud.ListView):
        filterset_class = MesaDiretoraFilterSet
        paginate_by = None

        def get_id_legislatura_atual(self):
            return Legislatura.objects.filter(
                data_inicio__lte=timezone.now()
            ).order_by('-data_inicio').values_list('id', flat=True).first()

        def get_filterset_kwargs(self, filterset_class):
            fk = super().get_filterset_kwargs(filterset_class)
            if 'legislatura' not in self.request.GET and 'mesa' not in self.request.GET:
                fk['data'] = {'legislatura': self.get_id_legislatura_atual()}
            elif 'legislatura' not in self.request.GET and 'mesa' in self.request.GET:
                legislatura_da_mesa = Legislatura.objects.filter(
                    mesadiretora_set__id=self.request.GET['mesa']
                ).values_list('id', flat=True).first()
                if not legislatura_da_mesa:
                    raise Http404("MesaDiretora {} não encontrada.".format(self.request.GET['mesa']))
                fk['data'] = {'legislatura': legislatura_da_mesa}
            return fk

        def get_queryset(self):
            return super().get_queryset().prefetch_related(
                'composicaomesa_set__parlamentar__filiacao_set__partido',
                'composicaomesa_set__cargo'
                )

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            context['title'] = ' '
            return context

        def get(self, request, *args, **kwargs):
            return FilterView.get(self, request, *args, **kwargs)

    class UpdateView(Crud.UpdateView):
        form_class = MesaDiretoraForm

    class CreateView(Crud.CreateView):
        form_class = MesaDiretoraForm

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

class ComposicaoMesaCrud(MasterDetailCrud):
    model = ComposicaoMesa
    parent_field = 'mesa_diretora'
    help_topic = 'mesa_diretora'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = 'parlamentares/subnav_mesa.yaml'
            return context

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = ComposicaoMesaForm

        def get_initial(self):
            initial = super().get_initial()
            initial['mesa_diretora'] = self.object.mesa_diretora
            return initial

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ComposicaoMesaForm

        def get_initial(self):
            initial = super().get_initial()
            initial['mesa_diretora'] = MesaDiretora.objects.get(pk=self.kwargs['pk'])
            return initial

def partido_parlamentar_sessao_legislativa(sessao, parlamentar):
    """
        Função para descobrir o partido do parlamentar durante
        o período de uma dada Sessão Legislativa
    """

    # As condições para mostrar a filiação são:
    # A data de filiacao deve ser menor que a data de fim
    # da sessao legislativa e data de desfiliação deve nula, ou maior,
    # ou igual a data de fim da sessao
    logger = logging.getLogger(__name__)
    try:
        logger.debug("Tentando obter filiação do parlamentar com (data<={} e data_desfiliacao>={}) "
                     "ou (data<={} e data_desfiliacao=Null))."
                     .format(sessao.data_fim, sessao.data_fim, sessao.data_fim))

        logger.info("Tentando obter filiação correspondente.")
        filiacao = parlamentar.filiacao_set.get(Q(
            data__lte=sessao.data_fim,
            data_desfiliacao__gte=sessao.data_fim) | Q(
            data__lte=sessao.data_fim,
            data_desfiliacao__isnull=True))

    # Caso não exista filiação com essas condições
    except ObjectDoesNotExist:
        logger.error("Filiação do parlamentar com (data<={} e data_desfiliacao>={}) "
                     "ou (data<={} e data_desfiliacao=Null não encontrada. Retornando vazio."
                     .format(sessao.data_fim, sessao.data_fim, sessao.data_fim))
        return ''

    # Caso exista mais de uma filiação nesse intervalo
    # Entretanto, NÃO DEVE OCORRER
    except MultipleObjectsReturned:
        logger.error("O Parlamentar com (data<={} e data_desfiliacao>={}) "
                     "ou (data<={} e data_desfiliacao=Null possui duas filiações conflitantes."
                     .format(sessao.data_fim, sessao.data_fim, sessao.data_fim))
        return 'O Parlamentar possui duas filiações conflitantes'

    # Caso encontre UMA filiação nessas condições
    else:
        logger.info("Filiação do parlamentar com (data<={} e data_desfiliacao>={}) "
                    "ou (data<={} e data_desfiliacao=Null encontrada com sucesso."
                    .format(sessao.data_fim, sessao.data_fim, sessao.data_fim))
        return filiacao.partido.sigla


class VincularParlamentarView(PermissionRequiredMixin, FormView):
    logger = logging.getLogger(__name__)
    form_class = VincularParlamentarForm
    template_name = 'parlamentares/vincular_parlamentar.html'
    permission_required = ('parlamentares.add_parlamentar',)

    def get_success_url(self):
        return reverse('sapl.parlamentares:parlamentar_list')

    def form_valid(self, form):
        kwargs = {
            'parlamentar': form.cleaned_data['parlamentar'],
            'legislatura': form.cleaned_data['legislatura'],
            'data_inicio_mandato': form.cleaned_data['legislatura'].data_inicio,
            'data_fim_mandato': form.cleaned_data['legislatura'].data_fim
        }

        data_expedicao_diploma = form.cleaned_data.get(
            'data_expedicao_diploma')
        if data_expedicao_diploma:
            kwargs.update({'data_expedicao_diploma': data_expedicao_diploma})

        mandato = Mandato.objects.create(**kwargs)
        mandato.save()

        return HttpResponseRedirect(self.get_success_url())


class BlocoCrud(CrudAux):
    model = Bloco
    public = [RP_DETAIL, RP_LIST]

    class CreateView(CrudAux.CreateView):
        form_class = BlocoForm

        def get_success_url(self):
            return reverse('sapl.parlamentares:bloco_list')

    class UpdateView(CrudAux.UpdateView):
        form_class = BlocoForm

        def get_success_url(self):
            return reverse('sapl.parlamentares:bloco_list')


class BlocoMembroCrud(MasterDetailCrud):
    model = BlocoMembro
    parent_field = 'bloco'
    help_topic = 'bloco_membros'
    public = [RP_LIST, RP_DETAIL]

    class CreateView(MasterDetailCrud.CreateView):
        form_class = BlocoMembroForm

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

        def get_initial(self):
            self.initial['bloco'] = Bloco.objects.get(pk=self.kwargs['pk'])
            return self.initial

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = BlocoMembroForm

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

    class DetailView(MasterDetailCrud.DetailView):
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

    class ListView(MasterDetailCrud.ListView):
        layout_key = 'BlocoMembroList'
        ordering = ('-cargo__cargo_unico', 'parlamentar')

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context


def get_sessoes_legislatura(request):
    legislatura_id = request.GET['legislatura']

    json_response = {'sessoes_legislativas': []}
    for s in SessaoLegislativa.objects.filter(legislatura_id=legislatura_id):
        json_response['sessoes_legislativas'].append((s.id, str(s)))

    return JsonResponse(json_response)
