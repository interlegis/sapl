
from django.core.urlresolvers import reverse
from django.db.models import F
from django.views.generic import ListView

from sapl.crud.base import Crud, CrudAux, MasterDetailCrud, RP_DETAIL, RP_LIST
from sapl.materia.models import MateriaLegislativa, Tramitacao

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
    public = [RP_DETAIL, ]
    ListView = None
    is_m2m = True

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['composicao', 'parlamentar', 'cargo']


class ComposicaoCrud(MasterDetailCrud):
    model = Composicao
    parent_field = 'comissao'
    model_set = 'participacao_set'
    public = [RP_LIST, RP_DETAIL, ]


class ComissaoCrud(Crud):
    model = Comissao
    help_path = 'modulo_comissoes'
    public = [RP_LIST, RP_DETAIL, ]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['nome', 'sigla', 'tipo', 'data_criacao', 'ativa']
        ordering = '-ativa', 'sigla'


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
