
from django.core.urlresolvers import reverse
from django.db.models import F
from django.http.response import HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import ListView
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin

from sapl.base.models import AppConfig as AppsAppConfig
from sapl.comissoes.apps import AppConfig
from sapl.comissoes.forms import (ComissaoForm, ComposicaoForm,
                                  DocumentoAcessorioCreateForm,
                                  DocumentoAcessorioEditForm,
                                  ParticipacaoCreateForm, ParticipacaoEditForm,
                                  PeriodoForm, ReuniaoForm)
from sapl.crud.base import (RP_DETAIL, RP_LIST, Crud, CrudAux,
                            MasterDetailCrud,
                            PermissionRequiredForAppCrudMixin)
from sapl.materia.models import MateriaLegislativa, Tramitacao

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
        template_name = "comissoes/composicao_list.html"
        paginate_by = None

        def take_composicao_pk(self):
            try:
                return int(self.request.GET['pk'])
            except:
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


class MateriasTramitacaoListView(ListView):
    template_name = "comissoes/materias_em_tramitacao.html"
    paginate_by = 10

    def get_queryset(self):
        # FIXME: Otimizar consulta
        ts = Tramitacao.objects.order_by(
            'materia', '-data_tramitacao', '-id').annotate(
            comissao=F('unidade_tramitacao_destino__comissao')).distinct(
                'materia').values_list('materia', 'comissao')

        ts = list(filter(lambda x: x[1] == int(self.kwargs['pk']), ts))
        ts = list(zip(*ts))
        ts = ts[0] if ts else []

        materias = MateriaLegislativa.objects.filter(
            pk__in=ts).order_by('tipo', '-ano', '-numero')

        return materias

    def get_context_data(self, **kwargs):
        context = super(
            MateriasTramitacaoListView, self).get_context_data(**kwargs)
        context['object'] = Comissao.objects.get(id=self.kwargs['pk'])
        return context


class ReuniaoCrud(MasterDetailCrud):
    model = Reuniao
    parent_field = 'comissao'
    model_set = 'documentoacessorio_set'
    public = [RP_LIST, RP_DETAIL, ]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data', 'nome', 'tema']

    class ListView(MasterDetailCrud.ListView):
        paginate_by = 10

        def take_reuniao_pk(self):
            try:
                return int(self.request.GET['pk'])
            except:
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
