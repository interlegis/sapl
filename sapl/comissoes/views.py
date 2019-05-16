import logging

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import F
from django.http.response import HttpResponseRedirect, JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import ListView, CreateView, DeleteView
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin, UpdateView
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import AppConfig as AppsAppConfig
from sapl.comissoes.apps import AppConfig
from sapl.comissoes.forms import (ComissaoForm, ComposicaoForm,
                                  DocumentoAcessorioCreateForm,
                                  DocumentoAcessorioEditForm,
                                  ParticipacaoCreateForm, ParticipacaoEditForm,
                                  PeriodoForm, ReuniaoForm, PautaReuniaoForm)
from sapl.crud.base import (RP_DETAIL, RP_LIST, Crud, CrudAux,
                            MasterDetailCrud,
                            PermissionRequiredForAppCrudMixin)
from sapl.materia.models import MateriaLegislativa, Tramitacao, PautaReuniao

from .models import (CargoComissao, Comissao, Composicao, DocumentoAcessorio,
                     Participacao, Periodo, Reuniao, TipoComissao)


def pegar_url_composicao(pk):
    participacao = Participacao.objects.get(id=pk)
    comp_pk = participacao.composicao.pk
    url = reverse('sapl.comissoes:composicao_detail', kwargs={'pk': comp_pk})
    return url


def pegar_url_reuniao(pk):
    documentoacessorio = DocumentoAcessorio.objects.get(id=pk)
    r_pk = documentoacessorio.reuniao.pk
    url = reverse('sapl.comissoes:reuniao_detail', kwargs={'pk': r_pk})
    return url

CargoCrud = CrudAux.build(CargoComissao, 'cargo_comissao')

TipoComissaoCrud = CrudAux.build(
    TipoComissao, 'tipo_comissao', list_field_names=[
        'sigla', 'nome', 'natureza', 'dispositivo_regimental'])


class PeriodoComposicaoCrud(CrudAux):
    model = Periodo

    class CreateView(CrudAux.CreateView):
        form_class = PeriodoForm

    class UpdateView(CrudAux.UpdateView):
        form_class = PeriodoForm

    # class ListView(CrudAux.ListView):


class ParticipacaoCrud(MasterDetailCrud):
    model = Participacao
    parent_field = 'composicao__comissao'
    public = [RP_DETAIL, ]
    ListView = None
    link_return_to_parent_field = True

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['composicao', 'parlamentar', 'cargo']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ParticipacaoCreateForm

        def get_initial(self):
            initial = super().get_initial()
            initial['parent_pk'] = self.kwargs['pk']
            return initial

    class UpdateView(MasterDetailCrud.UpdateView):
        layout_key = 'ParticipacaoEdit'
        form_class = ParticipacaoEditForm

    class DeleteView(MasterDetailCrud.DeleteView):

        def get_success_url(self):
            composicao_comissao_pk = self.object.composicao.comissao.pk
            composicao_pk = self.object.composicao.pk
            return '{}?pk={}'.format(reverse('sapl.comissoes:composicao_list',
                                             args=[composicao_comissao_pk]),
                                     composicao_pk)


class ComposicaoCrud(MasterDetailCrud):
    model = Composicao
    parent_field = 'comissao'
    model_set = 'participacao_set'
    public = [RP_LIST, RP_DETAIL, ]

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ComposicaoForm

        def get_initial(self):
            comissao = Comissao.objects.get(id=self.kwargs['pk'])
            return {'comissao': comissao}

    class ListView(MasterDetailCrud.ListView):
        logger = logging.getLogger(__name__)
        template_name = "comissoes/composicao_list.html"
        paginate_by = None

        def take_composicao_pk(self):

            username = self.request.user.username
            try:
                self.logger.debug('user=' + username + '. Tentando obter pk da composição.')
                return int(self.request.GET['pk'])
            except Exception as e:
                self.logger.error('user=' + username + '. Erro ao obter pk da composição. Retornado 0. ' + str(e))
                return 0

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            composicao_pk = self.take_composicao_pk()

            if composicao_pk == 0:
                # Composicao eh ordenada por Periodo, que por sua vez esta em
                # ordem descrescente de data de inicio (issue #1920)
                ultima_composicao = context['composicao_list'].first()
                if ultima_composicao:
                    context['composicao_pk'] = ultima_composicao.pk
                else:
                    context['composicao_pk'] = 0
            else:
                context['composicao_pk'] = composicao_pk

            context['participacao_set'] = Participacao.objects.filter(
                composicao__pk=context['composicao_pk']
            ).order_by('id')
            return context


class ComissaoCrud(Crud):
    model = Comissao
    help_topic = 'modulo_comissoes'
    public = [RP_LIST, RP_DETAIL, ]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['nome', 'sigla', 'tipo',
                            'data_criacao', 'data_extincao', 'ativa']
        ordering = '-ativa', 'sigla'

    class CreateView(Crud.CreateView):
        form_class = ComissaoForm

        def form_valid(self, form):
            return super(Crud.CreateView, self).form_valid(form)

    class UpdateView(Crud.UpdateView):
        form_class = ComissaoForm

        def form_valid(self, form):
            return super(Crud.UpdateView, self).form_valid(form)


def lista_materias_comissao(comissao_pk):
    ts = Tramitacao.objects.order_by(
        'materia', '-data_tramitacao', '-id').annotate(
        comissao=F('unidade_tramitacao_destino__comissao')).distinct(
            'materia').values_list('materia', 'comissao')

    ts = [m for (m,c) in ts if c == int(comissao_pk)]

    materias = MateriaLegislativa.objects.filter(
        pk__in=ts).order_by('tipo', '-ano', '-numero')

    return materias


class MateriasTramitacaoListView(ListView):
    template_name = "comissoes/materias_em_tramitacao.html"
    paginate_by = 10

    def get_queryset(self):
        return lista_materias_comissao(self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(
            MateriasTramitacaoListView, self).get_context_data(**kwargs)
        context['object'] = Comissao.objects.get(id=self.kwargs['pk'])
        context['qtde'] = self.object_list.count()
        return context


class ReuniaoCrud(MasterDetailCrud):
    model = Reuniao
    parent_field = 'comissao'
    public = [RP_LIST, RP_DETAIL, ]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data', 'nome', 'tema', 'upload_ata']
        ordering = '-data'

    class DetailView(MasterDetailCrud.DetailView):
        template_name = "comissoes/reuniao_detail.html"

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            docs = []
            documentos = DocumentoAcessorio.objects.filter(reuniao=self.kwargs['pk']).order_by('nome')
            docs.extend(documentos)

            context['docs'] = docs
            context['num_docs'] = len(docs)

            mats = []
            materias_pauta = PautaReuniao.objects.filter(reuniao=self.kwargs['pk'])
            materias_pk = [materia_pauta.materia.pk for materia_pauta in materias_pauta]
            
            context['mats'] = MateriaLegislativa.objects.filter(
                pk__in=materias_pk
            ).order_by('tipo', '-ano', '-numero')
            context['num_mats'] = len(context['mats'])

            context['reuniao_pk'] = self.kwargs['pk']
            
            return context

    class ListView(MasterDetailCrud.ListView):
        logger = logging.getLogger(__name__)
        paginate_by = 10

        def take_reuniao_pk(self):

            username = self.request.user.username
            try:
                self.logger.debug('user=' + username + '. Tentando obter pk da reunião.')
                return int(self.request.GET['pk'])
            except Exception as e:
                self.logger.error('user=' + username + '. Erro ao obter pk da reunião. Retornado 0. ' + str(e))
                return 0

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            reuniao_pk = self.take_reuniao_pk()

            if reuniao_pk == 0:
                ultima_reuniao = list(context['reuniao_list'])
                if len(ultima_reuniao) > 0:
                    ultimo = ultima_reuniao[-1]
                    context['reuniao_pk'] = ultimo.pk
                else:
                    context['reuniao_pk'] = 0
            else:
                context['reuniao_pk'] = reuniao_pk

            context['documentoacessorio_set'] = DocumentoAcessorio.objects.filter(
                reuniao__pk=context['reuniao_pk']
            ).order_by('id')
            return context

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = ReuniaoForm

        def get_initial(self):
            return {'comissao': self.object.comissao}

    class CreateView(MasterDetailCrud.CreateView):
        form_class = ReuniaoForm

        def get_initial(self):
            comissao = Comissao.objects.get(id=self.kwargs['pk'])

            return {'comissao': comissao}


class RemovePautaView(PermissionRequiredMixin, CreateView):
    model = PautaReuniao
    form_class = PautaReuniaoForm
    template_name = 'comissoes/pauta.html'
    permission_required = ('comissoes.add_reuniao', )

    def get_context_data(self, **kwargs):
        context = super(
            RemovePautaView, self
        ).get_context_data(**kwargs)

        # Remove = 0; Adiciona = 1
        context['opcao'] = 0

        context['object'] = Reuniao.objects.get(pk=self.kwargs['pk'])
        context['root_pk'] = context['object'].comissao.pk

        materias_pauta = PautaReuniao.objects.filter(reuniao=context['object'])
        materias_pk = [materia_pauta.materia.pk for materia_pauta in materias_pauta]
        
        context['materias'] = MateriaLegislativa.objects.filter(
            pk__in=materias_pk
        ).order_by('tipo', '-ano', '-numero') 
        context['num_materias'] = len(context['materias'])

        return context

    def post(self, request, *args, **kwargs):
        success_url = reverse('sapl.comissoes:reuniao_detail', kwargs={'pk':kwargs['pk']})
        marcadas = request.POST.getlist('materia_id')

        if not marcadas:
            msg=_('Nenhuma matéria foi selecionada.')
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(success_url)

        reuniao = Reuniao.objects.get(pk=kwargs['pk'])
        for materia in MateriaLegislativa.objects.filter(id__in=marcadas):
            PautaReuniao.objects.filter(reuniao=reuniao,materia=materia).delete()

        msg=_('Matéria(s) removida(s) com sucesso!')
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(success_url)


class AdicionaPautaView(PermissionRequiredMixin, CreateView):
    model = PautaReuniao
    form_class = PautaReuniaoForm
    template_name = 'comissoes/pauta.html'
    permission_required = ('comissoes.add_reuniao', )

    def get_context_data(self, **kwargs):
        context = super(
            AdicionaPautaView, self
        ).get_context_data(**kwargs)

        # Adiciona = 1; Remove = 0
        context['opcao'] = 1

        context['object'] = Reuniao.objects.get(pk=self.kwargs['pk'])
        context['root_pk'] = context['object'].comissao.pk

        materias_comissao = lista_materias_comissao(context['object'].comissao.pk)
        materias_pauta = PautaReuniao.objects.filter(reuniao=context['object'])

        nao_listar = [mp.materia.pk for mp in materias_pauta]
        context['materias'] = materias_comissao.exclude(pk__in=nao_listar)
        context['num_materias'] = len(context['materias'])

        return context
    
    def post(self, request, *args, **kwargs):
        success_url = reverse('sapl.comissoes:reuniao_detail', kwargs={'pk':kwargs['pk']}) 
        marcadas = request.POST.getlist('materia_id')

        if not marcadas:
            msg = _('Nenhuma máteria foi selecionada.')
            messages.add_message(request, messages.WARNING, msg)
            return HttpResponseRedirect(success_url)
            
        reuniao = Reuniao.objects.get(pk=kwargs['pk'])
        pautas = []
        for materia in MateriaLegislativa.objects.filter(id__in=marcadas):
                 pauta = PautaReuniao()
                 pauta.reuniao = reuniao
                 pauta.materia = materia
                 pautas.append(pauta)
        PautaReuniao.objects.bulk_create(pautas)
        
        msg = _('Matéria(s) adicionada(s) com sucesso!')
        messages.add_message(request, messages.SUCCESS, msg)
        return HttpResponseRedirect(success_url)


class DocumentoAcessorioCrud(MasterDetailCrud):
    model = DocumentoAcessorio
    parent_field = 'reuniao__comissao'
    public = [RP_DETAIL, ]
    ListView = None
    link_return_to_parent_field = True

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['nome', 'tipo', 'data', 'autor', 'arquivo']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = DocumentoAcessorioCreateForm

        def get_initial(self):
            initial = super().get_initial()
            initial['parent_pk'] = self.kwargs['pk']
            return initial

    class UpdateView(MasterDetailCrud.UpdateView):
        layout_key = 'DocumentoAcessorioEdit'
        form_class = DocumentoAcessorioEditForm

    class DeleteView(MasterDetailCrud.DeleteView):

        def delete(self, *args, **kwargs):
            obj = self.get_object()
            obj.delete()
            return HttpResponseRedirect(
                reverse('sapl.comissoes:reuniao_detail',
                        kwargs={'pk': obj.reuniao.pk}))


def get_participacoes_comissao(request):
    parlamentares = []

    composicao_id = request.GET.get('composicao_id')
    if composicao_id:
        parlamentares = [{'nome': p.parlamentar.nome_parlamentar, 'id': p.parlamentar.id} for p in
                         Participacao.objects.filter(composicao_id=composicao_id).order_by(
                             'parlamentar__nome_parlamentar')]

    return JsonResponse(parlamentares, safe=False)
