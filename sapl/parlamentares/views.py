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
from django.http import JsonResponse
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
from sapl.utils import (parlamentares_ativos, show_results_filter_set)

from .forms import (ColigacaoFilterSet, FiliacaoForm, FrenteForm, LegislaturaForm, MandatoForm,
                    ParlamentarCreateForm, ParlamentarForm, VotanteForm,
                    ParlamentarFilterSet, PartidoFilterSet, VincularParlamentarForm,
                    BlocoForm, FrenteParlamentarForm, BlocoMembroForm)
from .models import (CargoMesa, Coligacao, ComposicaoColigacao, ComposicaoMesa,
                     Dependente, Filiacao, Frente, Legislatura, Mandato,
                     NivelInstrucao, Parlamentar, Partido, SessaoLegislativa,
                     SituacaoMilitar, TipoAfastamento, TipoDependente, Votante,
                     Bloco, FrenteCargo, FrenteParlamentar, BlocoCargo, BlocoMembro, MesaDiretora)

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
    model = Frente
    is_m2m = True
    parent_field = 'parlamentares'
    CreateView, UpdateView, DeleteView = None, None, None

    class BaseMixin(Crud.PublicMixin, MasterDetailCrud.BaseMixin):
        list_field_names = ['nome', 'data_criacao', 'data_extincao']

        @classmethod
        def url_name(cls, suffix):
            return '%s_parlamentar_%s' % (cls.model._meta.model_name, suffix)


class RelatoriaParlamentarCrud(CrudBaseForListAndDetailExternalAppView):
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
            'filiacao_atual',
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
                              parlamentar.filiacao_atual == partido.sigla]
    return render(request, template_name, {'partido': partido, 'parlamentares': parlamentares_filiados})


class MesaDiretoraView(FormView):
    template_name = 'parlamentares/composicaomesa_form.html'
    success_url = reverse_lazy('sapl.parlamentares:mesa_diretora')
    logger = logging.getLogger(__name__)

    def get_template_names(self):
        if self.request.user.has_perm('parlamentares.change_composicaomesa'):
            if 'iframe' not in self.request.GET:
                if not self.request.session.get('iframe'):
                    return 'parlamentares/composicaomesa_form.html'
            elif self.request.GET['iframe'] == '0':
                return 'parlamentares/composicaomesa_form.html'

        return 'parlamentares/public_composicaomesa_form.html'

    # Essa função avisa quando se pode compor uma Mesa Legislativa
    def validation(self, request):
        username = request.user.username
        self.logger.info('user=' + username + '. Não há nenhuma Sessão Legislativa cadastrada. ' +
                         'Só é possível compor uma Mesa Diretora quando ' +
                         'há uma Sessão Legislativa cadastrada.')
        mensagem = _('Não há nenhuma Sessão Legislativa cadastrada. ' +
                     'Só é possível compor uma Mesa Diretora quando ' +
                     'há uma Sessão Legislativa cadastrada.')
        messages.add_message(request, messages.INFO, mensagem)

        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all(
            ).order_by('-numero'),
                'legislatura_selecionada': Legislatura.objects.last(),
                'cargos_vagos': CargoMesa.objects.all()})

    @xframe_options_exempt
    def get(self, request, *args, **kwargs):

        if (not Legislatura.objects.exists() or
                not SessaoLegislativa.objects.exists()):
            return self.validation(request)

        legislatura = Legislatura.objects.first()
        sessoes = SessaoLegislativa.objects.filter(
            legislatura=legislatura).order_by("data_inicio")

        year = timezone.now().year

        sessao_atual = sessoes.filter(data_inicio__year__lte=year).exclude(
            data_inicio__gt=timezone.now()).order_by('-data_inicio').first()

        mesa_diretora = sessao_atual.mesadiretora_set.order_by(
            '-data_inicio').first() if sessao_atual else None

        composicao_mesa = ComposicaoMesa.objects.select_related('cargo', 'parlamentar').filter(
            mesa_diretora=mesa_diretora).order_by('cargo__id_ordenacao', 'cargo_id')

        cargos_ocupados = [m.cargo for m in composicao_mesa]
        cargos = CargoMesa.objects.all()
        cargos_vagos = list(set(cargos) - set(cargos_ocupados))

        parlamentares = legislatura.mandato_set.all()
        parlamentares_ocupados = [m.parlamentar for m in composicao_mesa]
        parlamentares_vagos = list(
            set(
                [p.parlamentar for p in parlamentares if p.parlamentar.ativo]) - set(
                parlamentares_ocupados))
        parlamentares_vagos.sort(key=lambda x: x.nome_parlamentar)
        # Se todos os cargos estiverem ocupados, a listagem de parlamentares
        # deve ser renderizada vazia
        if not cargos_vagos:
            parlamentares_vagos = []

        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all(
            ).order_by('-numero'),
                'legislatura_selecionada': legislatura,
                'sessoes': sessoes,
                'sessao_selecionada': sessao_atual,
                'composicao_mesa': composicao_mesa,
                'parlamentares': parlamentares_vagos,
                'cargos_vagos': cargos_vagos
            })


def altera_field_mesa(request):
    """
        Essa função lida com qualquer alteração nos campos
        da Mesa Diretora, após qualquer
        operação (Legislatura/Sessão/Inclusão/Remoção),
        atualizando os campos após cada alteração
    """
    # TODO: Adicionar opção de selecionar mesa diretora no CRUD

    logger = logging.getLogger(__name__)
    legislatura = request.GET['legislatura']
    sessoes = SessaoLegislativa.objects.filter(
        legislatura=legislatura).order_by('-data_inicio')
    username = request.user.username

    if not sessoes:
        return JsonResponse({'msg': ('Nenhuma sessão encontrada!', 0)})

    # Verifica se já tem uma sessão selecionada. Ocorre quando
    # é alterado o campo de sessão ou feita alguma operação
    # de inclusão/remoção.
    if request.GET['sessao']:
        sessao_selecionada = SessaoLegislativa.objects.get(
            id=request.GET['sessao'])

    # Caso a mudança tenha sido no campo legislatura, a sessão
    # atual deve ser a primeira daquela legislatura
    else:
        year = timezone.now().year
        logger.debug(
            "user={}. Tentando obter id de sessoes com data_inicio.ano={}.".format(username, year))
        sessao_selecionada = sessoes.filter(data_inicio__year=year).first()
        if not sessao_selecionada:
            logger.error("user=" + username + ". Id de sessoes com data_inicio.ano={} não encontrado. "
                                              "Selecionado o ID da primeira sessão.".format(year))
            sessao_selecionada = sessoes.first()

    mesa_diretora = request.GET.get('mesa_diretora')

    # Mesa nao deve ser informada ainda
    if not mesa_diretora:
        # Cria nova mesa diretora ou retorna a primeira
        mesa_diretora, _ = MesaDiretora.objects.get_or_create(
            sessao_legislativa=sessao_selecionada)

        # TODO: quando a mesa for criada explicitamente em tabelas auxiliares,
        #      deve-se somente tentar recuperar a mesa, e caso nao exista
        #      retornar o erro abaixo
        # return JsonResponse({'msg': ('Nenhuma mesa encontrada na sessão!')})
    else:
        try:
            mesa_diretora = MesaDiretora.objects.get(
                id=mesa_diretora, sessao_legislativa=sessao_selecionada)
        except ObjectDoesNotExist:
            mesa_diretora = MesaDiretora.objects.filter(
                sessao_legislativa=sessao_selecionada).first()

    # Atualiza os componentes da view após a mudança
    composicao_mesa = ComposicaoMesa.objects.select_related('cargo', 'parlamentar').filter(
        mesa_diretora=mesa_diretora).order_by('cargo_id')

    cargos_ocupados = [m.cargo for m in composicao_mesa]
    cargos = CargoMesa.objects.all()
    cargos_vagos = list(set(cargos) - set(cargos_ocupados))

    parlamentares = Legislatura.objects.get(
        id=legislatura).mandato_set.all()
    parlamentares_ocupados = [m.parlamentar for m in composicao_mesa]
    parlamentares_vagos = list(
        set(
            [p.parlamentar for p in parlamentares]) - set(
            parlamentares_ocupados))

    parlamentares_vagos.sort(key=lambda x: x.nome_parlamentar)
    lista_sessoes = [(s.id, s.__str__()) for s in sessoes]
    lista_composicao = [(c.id, c.parlamentar.__str__(),
                         c.cargo.__str__()) for c in composicao_mesa]
    lista_parlamentares = [(
        p.id, p.__str__()) for p in parlamentares_vagos]
    lista_cargos = [(c.id, c.__str__()) for c in cargos_vagos]

    return JsonResponse(
        {'lista_sessoes': lista_sessoes,
         'lista_composicao': lista_composicao,
         'lista_parlamentares': lista_parlamentares,
         'lista_cargos': lista_cargos,
         'sessao_selecionada': sessao_selecionada.id,
         'msg': ('', 1)})


def insere_parlamentar_composicao(request):
    """
        Essa função lida com qualquer operação de inserção
        na composição da Mesa Diretora
    """
    logger = logging.getLogger(__name__)
    username = request.user.username
    if request.user.has_perm(
            '%s.add_%s' % (
                AppConfig.label, ComposicaoMesa._meta.model_name)):
        composicao = ComposicaoMesa()

        try:
            # logger.debug(
            #    "user=" + username + ". Tentando obter SessaoLegislativa com id={}.".format(request.POST['sessao']))
            mesa_diretora, _ = MesaDiretora.objects.get_or_create(
                sessao_legislativa_id=int(request.POST['sessao']))
            composicao.mesa_diretora = mesa_diretora
        except MultiValueDictKeyError:
            logger.error(
                "user=" + username + ". 'MultiValueDictKeyError', nenhuma sessão foi inserida!")
            return JsonResponse({'msg': ('Nenhuma sessão foi inserida!', 0)})

        try:
            logger.debug(
                "user=" + username + ". Tentando obter Parlamentar com id={}.".format(request.POST['parlamentar']))
            composicao.parlamentar = Parlamentar.objects.get(
                id=int(request.POST['parlamentar']))
        except MultiValueDictKeyError:
            logger.error(
                "user=" + username + ". 'MultiValueDictKeyError', nenhum parlamentar foi inserido!")
            return JsonResponse({
                'msg': ('Nenhum parlamentar foi inserido!', 0)})

        try:
            logger.info("user=" + username +
                        ". Tentando obter CargoMesa com id={}.".format(request.POST['cargo']))
            composicao.cargo = CargoMesa.objects.get(
                id=int(request.POST['cargo']))
            parlamentar_ja_inserido = ComposicaoMesa.objects.filter(
                mesa_diretora=mesa_diretora,
                cargo=composicao.cargo).exists()

            if parlamentar_ja_inserido:
                return JsonResponse({'msg': ('Parlamentar já inserido!', 0)})
            composicao.save()

        except MultiValueDictKeyError:
            logger.error("user=" + username +
                         ". 'MultiValueDictKeyError', nenhum cargo foi inserido!")
            return JsonResponse({'msg': ('Nenhum cargo foi inserido!', 0)})

        logger.info("user=" + username + ". Parlamentar inserido com sucesso!")
        return JsonResponse({'msg': ('Parlamentar inserido com sucesso!', 1)})

    else:
        logger.error("user=" + username +
                     " não tem permissão para esta operação!")
        return JsonResponse(
            {'msg': ('Você não tem permissão para esta operação!', 0)})


def remove_parlamentar_composicao(request):
    """
        Essa função lida com qualquer operação de remoção
        na composição da Mesa Diretora
    """
    logger = logging.getLogger(__name__)
    username = request.user.username
    if request.POST and request.user.has_perm(
            '%s.delete_%s' % (
                AppConfig.label, ComposicaoMesa._meta.model_name)):

        if 'composicao_mesa' in request.POST:
            try:
                logger.debug("user=" + username + ". Tentando obter ComposicaoMesa com id={}.".format(
                    request.POST['composicao_mesa']))
                composicao = ComposicaoMesa.objects.get(
                    id=request.POST['composicao_mesa'])
            except ObjectDoesNotExist:
                logger.error(
                    "user=" + username +
                    ". ComposicaoMesa com id={} não encontrada, portanto não pode ser removida."
                    .format(request.POST['composicao_mesa']))
                return JsonResponse(
                    {'msg': (
                        'Composição da Mesa não pôde ser removida!', 0)})

            composicao.delete()

            logger.info("user=" + username + ". ComposicaoMesa com id={} excluido com sucesso!".format(
                request.POST['composicao_mesa']))
            return JsonResponse(
                {'msg': (
                    'Parlamentar excluido com sucesso!', 1)})
        else:
            logger.info("user=" + username +
                        ". Nenhum parlamentar escolhido para ser excluído.")
            return JsonResponse(
                {'msg': (
                    'Selecione algum parlamentar para ser excluido!', 0)})


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


def altera_field_mesa_public_view(request):
    """
        Essa função lida com qualquer alteração nos campos
        da Mesa Diretora para usuários anônimos,
        atualizando os campos após cada alteração
    """

    # TODO: Adicionar opção de selecionar mesa diretora no CRUD

    logger = logging.getLogger(__name__)
    username = request.user.username
    legislatura = request.GET['legislatura']
    if legislatura:
        legislatura = Legislatura.objects.get(id=legislatura)
    else:
        legislatura = Legislatura.objects.order_by('-data_inicio').first()

    sessoes = legislatura.sessaolegislativa_set.filter(
        tipo='O').order_by('-data_inicio')

    if not sessoes:
        return JsonResponse({'msg': ('Nenhuma sessão encontrada!', 0)})

    # Verifica se já tem uma sessão selecionada. Ocorre quando é alterado o
    # campo de sessão

    sessao_selecionada = request.GET['sessao']
    if not sessao_selecionada:
        year = timezone.now().year
        logger.info(
            f"user={username}. Tentando obter sessões com data_inicio.ano = {year}.")
        sessao_selecionada = sessoes.filter(data_inicio__year=year).first()
        if sessao_selecionada is None:
            logger.error(f"user={username}. Sessões não encontradas com com data_inicio.ano = {year}. "
                         "Selecionado o id da primeira sessão.")
            sessao_selecionada = sessoes.first()
    else:
        sessao_selecionada = SessaoLegislativa.objects.get(
            id=sessao_selecionada)

    # Atualiza os componentes da view após a mudança
    lista_sessoes = [(s.id, s.__str__()) for s in sessoes]

    # Pegar Mesas diretoras da sessao
    mesa_diretora = request.GET.get('mesa_diretora')

    # Mesa nao deve ser informada ainda
    if not mesa_diretora:
        try:
            mesa_diretora = sessao_selecionada.mesadiretora_set.first()
        except ObjectDoesNotExist:
            logger.error(
                f"user={username}. Mesa não encontrada com sessão Nº {sessao_selecionada.id}. ")
    else:
        # Cria nova mesa diretora ou retorna a primeira
        mesa_diretora, _ = MesaDiretora.objects.get_or_create(
            sessao_legislativa=sessao_selecionada)

        # TODO: quando a mesa for criada explicitamente em tabelas auxiliares,
        #      deve-se somente tentar recuperar a mesa, e caso nao exista
        #      retornar o erro abaixo
        #    logger.error(f"user={username}. Mesa Nº {mesa_diretora} não encontrada na sessão Nº {sessao_selecionada.id}. "
        #                "Selecionada a mesa com o primeiro id na sessão")

    composicao_mesa = ComposicaoMesa.objects.select_related('cargo', 'parlamentar').filter(
        mesa_diretora=mesa_diretora).order_by('cargo_id')
    cargos_ocupados = list(composicao_mesa.values_list(
        'cargo__id', 'cargo__descricao'))
    parlamentares_ocupados = list(composicao_mesa.values_list(
        'parlamentar__id', 'parlamentar__nome_parlamentar'))

    lista_fotos = []
    lista_partidos = []

    sessao = SessaoLegislativa.objects.get(id=sessao_selecionada.id)
    for p in parlamentares_ocupados:
        parlamentar = Parlamentar.objects.get(id=p[0])
        lista_partidos.append(
            partido_parlamentar_sessao_legislativa(sessao, parlamentar))
        if parlamentar.fotografia:
            try:
                logger.warning(f"Iniciando cropping da imagem {parlamentar.fotografia}")
                thumbnail_url = get_backend().get_thumbnail_url(
                    parlamentar.fotografia,
                    {
                        'size': (128, 128),
                        'box': parlamentar.cropping,
                        'crop': True,
                        'detail': True,
                    }
                )
                logger.warning(f"Cropping da imagem {parlamentar.fotografia} realizado com sucesso")
                lista_fotos.append(thumbnail_url)
            except Exception as e:
                logger.error(e)
                logger.error(
                    F'erro processando arquivo: {parlamentar.fotografia.path}')
        else:
            lista_fotos.append(None)

    return JsonResponse({
        'lista_parlamentares': parlamentares_ocupados,
        'lista_partidos': lista_partidos,
        'lista_cargos': cargos_ocupados,
        'lista_sessoes': lista_sessoes,
        'lista_fotos': lista_fotos,
        'sessao_selecionada': sessao_selecionada.id,
        'mesa_diretora': mesa_diretora.id,
        'msg': ('', 1)
    })


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
