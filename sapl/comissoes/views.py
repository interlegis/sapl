
from django.core.urlresolvers import reverse
from django.views.generic import ListView

from sapl.crud.base import Crud, CrudAux, MasterDetailCrud
from sapl.materia.models import MateriaLegislativa

from .models import (CargoComissao, Comissao, Composicao, Participacao,
                     Periodo, TipoComissao)


def pegar_url_composicao(pk):
    participacao = Participacao.objects.get(id=pk)
    comp_pk = participacao.composicao.pk
    url = reverse('sapl.comissoes:composicao_detail', kwargs={'pk': comp_pk})
    return url

CargoCrud = CrudAux.build(CargoComissao, 'cargo_comissao')
PeriodoComposicaoCrud = CrudAux.build(Periodo, 'periodo_composicao_comissao')

TipoComissaoCrud = CrudAux.build(
    TipoComissao, 'tipo_comissao', list_field_names=[
        'sigla', 'nome', 'natureza', 'dispositivo_regimental'])


class ParticipacaoCrud(MasterDetailCrud):
    model = Participacao
    parent_field = 'composicao__comissao'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['composicao', 'parlamentar', 'cargo']

    class DetailView(MasterDetailCrud.DetailView):
        permission_required = []


class ComposicaoCrud(MasterDetailCrud):
    model = Composicao
    parent_field = 'comissao'
    model_set = 'participacao_set'

    class ListView(MasterDetailCrud.ListView):
        permission_required = []

    class DetailView(MasterDetailCrud.DetailView):
        permission_required = []


class ComissaoCrud(Crud):
    model = Comissao
    help_path = 'modulo_comissoes'

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['nome', 'sigla', 'tipo', 'data_criacao', 'ativa']
        initial_order = '-ativa', 'sigla'

    class ListView(Crud.ListView):
        permission_required = []

    class DetailView(Crud.DetailView):
        permission_required = []


class MateriasTramitacaoListView(ListView):
    template_name = "comissoes/materias_em_tramitacao.html"
    paginate_by = 10

    def get_queryset(self):
        # FIXME: Otimizar consulta
        lista = []
        materias = MateriaLegislativa.objects.filter(tramitacao__isnull=False)
        for materia in materias:
            comissao = materia.tramitacao_set.last(
            ).unidade_tramitacao_local.comissao
            if comissao:
                if comissao.pk == int(self.kwargs['pk']):
                    lista.append(materia)
        return lista

    def get_context_data(self, **kwargs):
        context = super(
            MateriasTramitacaoListView, self).get_context_data(**kwargs)
        context['object'] = Comissao.objects.get(id=self.kwargs['pk'])
        return context
