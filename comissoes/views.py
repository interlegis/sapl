from django.core.urlresolvers import reverse
from django.views.generic import ListView

import crud.base
import crud.masterdetail
from crud.base import Crud
from crud.masterdetail import MasterDetailCrud
from materia.models import Tramitacao

from .models import (CargoComissao, Comissao, Composicao, Participacao,
                     Periodo, TipoComissao)

CargoCrud = Crud.build(CargoComissao, 'cargo_comissao')
PeriodoComposicaoCrud = Crud.build(Periodo, 'periodo_composicao_comissao')
TipoComissaoCrud = Crud.build(TipoComissao, 'tipo_comissao')


def pegar_url_composicao(pk):
    participacao = Participacao.objects.get(id=pk)
    comp_pk = participacao.composicao.pk
    url = reverse('comissoes:composicao_detail', kwargs={'pk': comp_pk})
    return url


class ParticipacaoCrud(MasterDetailCrud):
    model = Participacao
    parent_field = 'composicao'
    help_path = ''

    class CreateView(MasterDetailCrud.CreateView):

        def get_success_url(self):
            return reverse(
                'comissoes:composicao_detail', kwargs={'pk': self.kwargs['pk']}
            )

        def cancel_url(self):
            return reverse(
                'comissoes:composicao_detail', kwargs={'pk': self.kwargs['pk']}
            )

    class UpdateView(MasterDetailCrud.UpdateView):

        def get_success_url(self):
            return pegar_url_composicao(self.kwargs['pk'])

        def cancel_url(self):
            return pegar_url_composicao(self.kwargs['pk'])

    class DeleteView(MasterDetailCrud.DeleteView):

        def get_success_url(self):
            return pegar_url_composicao(self.kwargs['pk'])

        def cancel_url(self):
            return pegar_url_composicao(self.kwargs['pk'])


class ComposicaoCrud(MasterDetailCrud):
    model = Composicao
    parent_field = 'comissao'
    help_path = ''

    class DetailView(MasterDetailCrud.DetailView):

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            composicao = Composicao.objects.get(id=self.kwargs['pk'])
            context['participacoes'] = composicao.participacao_set.all()
            return self.render_to_response(context)


class ComissaoCrud(Crud):
    model = Comissao
    help_path = 'modulo_comissoes'

    class BaseMixin(crud.base.CrudBaseMixin):
        list_field_names = ['nome', 'sigla', 'tipo', 'data_criacao']


class MateriasTramitacaoListView(ListView):
    template_name = "comissoes/materias_em_tramitacao.html"
    paginate_by = 10

    def get_queryset(self):
        pk = self.kwargs['pk']
        tramitacoes = Tramitacao.objects.filter(
            unidade_tramitacao_local__comissao=pk)
        return tramitacoes

    def get_context_data(self, **kwargs):
        context = super(
            MateriasTramitacaoListView, self).get_context_data(**kwargs)
        context['object'] = Comissao.objects.get(id=self.kwargs['pk'])
        return context
