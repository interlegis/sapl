from itertools import chain

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django_filters.views import FilterView

from sapl.crud.base import (Crud, CrudBaseMixin, CrudCreateView,
                            CrudDetailView, CrudUpdateView)
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.sessao.models import (OrdemDia, PresencaOrdemDia, SessaoPlenaria,
                                SessaoPlenariaPresenca)
from sapl.utils import permissao_tb_aux

from .forms import (CasaLegislativaForm, RelatorioHistoricoTramitacaoFilterSet,
                    RelatorioMateriasPorAnoAutorTipoFilterSet,
                    RelatorioMateriasPorAutorFilterSet,
                    RelatorioMateriasTramitacaoilterSet,
                    RelatorioPresencaSessaoFilterSet)
from .models import CasaLegislativa


def get_casalegislativa():
    return CasaLegislativa.objects.first()


class RelatorioPresencaSessaoView(FilterView):
    model = SessaoPlenaria
    filterset_class = RelatorioPresencaSessaoFilterSet
    template_name = 'base/RelatorioPresencaSessao_filter.html'

    def calcular_porcentagem_presenca(self,
                                      parlamentares,
                                      total_sessao,
                                      total_ordem):
        for p in parlamentares.items():
            p[1].update({
                'porc_sessao': round(
                    p[1]['qtde_sessao'] * 100 / total_sessao, 1),
                'porc_ordem': round(p[1]['qtde_ordem'] * 100 / total_ordem, 1)
                })
        return parlamentares

    def get_context_data(self, **kwargs):
        context = super(RelatorioPresencaSessaoView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Presença dos parlamentares nas sessões')
        # =====================================================================
        # FIXME: Pensar em melhor forma de verificar se formulário está sendo
        # submetido.
        if 'salvar' in self.request.GET:
            qs1 = SessaoPlenariaPresenca.objects.filter(
                parlamentar__ativo=True,
                sessao_plenaria_id__in=context['object_list'])
            qs2 = PresencaOrdemDia.objects.filter(
                parlamentar__ativo=True,
                sessao_plenaria_id__in=context['object_list'])
            q = list(chain(list(qs1)+list(qs2)))

            parlamentares = {}

            total_sessao = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id__in=context['object_list'])
            total_sessao = len(total_sessao.order_by().values_list(
                'sessao_plenaria_id', flat=True).distinct())

            total_ordem = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id__in=context['object_list'])
            total_ordem = len(total_ordem.order_by().values_list(
                'sessao_plenaria_id', flat=True).distinct())

            for i in q:
                pid = i.parlamentar.id
                if not pid in parlamentares:
                    parlamentares[pid] = {
                        'nome': i.parlamentar.nome_parlamentar,
                        'partido': (
                            i.parlamentar.filiacao_set.first().partido.sigla
                            if i.parlamentar.filiacao_set.first()
                            else 'Sem Partido'),
                        'qtde_ordem': 0,
                        'qtde_sessao': 0}
                if isinstance(i, SessaoPlenariaPresenca):
                    parlamentares[pid]['qtde_sessao'] += 1
                elif isinstance(i, PresencaOrdemDia):
                    parlamentares[pid]['qtde_ordem'] += 1

            self.calcular_porcentagem_presenca(parlamentares,
                                               total_sessao,
                                               total_ordem)
            sorted(parlamentares.items(), key=lambda x: x[1]['nome'])

            context['total_ordem'] = total_ordem
            context['total_sessao'] = total_sessao
            context['parlamentares'] = parlamentares
            context['periodo'] = (self.request.GET['data_inicio_0'] +
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


class CasaLegislativaCrud(Crud):
    model = CasaLegislativa
    help_path = ''

    class BaseMixin(PermissionRequiredMixin, CrudBaseMixin):
        list_field_names = ['codigo', 'nome', 'sigla']

        def has_permission(self):
            if self.request.user.is_superuser:
                return True
            else:
                return False

    class CreateView(PermissionRequiredMixin, CrudCreateView):
        permission_required = {'base.add_casa_legislativa'}
        form_class = CasaLegislativaForm

    class UpdateView(PermissionRequiredMixin, CrudUpdateView):
        permission_required = {'base.change_casalegislativa'}
        form_class = CasaLegislativaForm

    class DetailView(CrudDetailView):
        form_class = CasaLegislativaForm

        def get(self, request, *args, **kwargs):
            return HttpResponseRedirect(
                reverse('sapl.base:casalegislativa_update',
                        kwargs={'pk': self.kwargs['pk']}))


class HelpView(PermissionRequiredMixin, TemplateView):
    # XXX treat non existing template as a 404!!!!

    def get_template_names(self):
        return ['ajuda/%s.html' % self.kwargs['topic']]


class SistemaView(PermissionRequiredMixin, TemplateView):
    template_name = 'sistema.html'
    permission_required = ''

    def has_permission(self):
        return permissao_tb_aux(self)
