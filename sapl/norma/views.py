from datetime import datetime

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import FormView, ListView
from django.views.generic.base import RedirectView

from sapl.base.models import AppConfig
from sapl.compilacao.views import IntegracaoTaView
from sapl.crud.base import (RP_DETAIL, RP_LIST, Crud, CrudAux,
                            MasterDetailCrud, make_pagination)
from sapl.norma.forms import NormaJuridicaForm

from .forms import NormaFilterSet
from .models import AssuntoNorma, NormaJuridica, TipoNormaJuridica

# LegislacaoCitadaCrud = Crud.build(LegislacaoCitada, '')
AssuntoNormaCrud = CrudAux.build(AssuntoNorma, 'assunto_norma_juridica',
                                 list_field_names=['assunto', 'descricao'])


TipoNormaCrud = CrudAux.build(
    TipoNormaJuridica, 'tipo_norma_juridica',
    list_field_names=['sigla', 'descricao', 'equivalente_lexml'])


class NormaPesquisaView(FilterView):
    model = NormaJuridica
    filterset_class = NormaFilterSet
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(NormaPesquisaView, self).get_context_data(**kwargs)

        context['title'] = _('Pesquisar Norma Jurídica')

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        return context


class NormaTaView(IntegracaoTaView):
    model = NormaJuridica
    model_type_foreignkey = TipoNormaJuridica
    map_fields = {
        'data': 'data',
        'ementa': 'ementa',
        'observacao': 'observacao',
        'numero': 'numero',
        'ano': 'ano',
    }

    map_funcs = {
        'publicacao_func': True
    }

    def get(self, request, *args, **kwargs):
        """
        Para manter a app compilacao isolada das outras aplicações,
        este get foi implementado para tratar uma prerrogativa externa
        de usuário.
        """
        if AppConfig.attr('texto_articulado_norma'):
            return IntegracaoTaView.get(self, request, *args, **kwargs)
        else:
            return self.get_redirect_deactivated()


class NormaCrud(Crud):
    model = NormaJuridica
    help_path = 'norma_juridica'
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'ementa']

        @property
        def list_url(self):
            return ''

        @property
        def search_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'norma_pesquisa'))

    class CreateView(Crud.CreateView):
        form_class = NormaJuridicaForm

        @property
        def cancel_url(self):
            return self.search_url

        @property
        def layout_key(self):
            return 'NormaJuridicaCreate'

    class ListView(Crud.ListView, RedirectView):

        def get_redirect_url(self, *args, **kwargs):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'norma_pesquisa'))

        def get(self, request, *args, **kwargs):
            return RedirectView.get(self, request, *args, **kwargs)

    class UpdateView(Crud.UpdateView):
        form_class = NormaJuridicaForm

        @property
        def layout_key(self):
            return 'NormaJuridicaCreate'

        def get_initial(self):
            norma = NormaJuridica.objects.get(id=self.kwargs['pk'])
            if norma.materia:
                self.initial['tipo_materia'] = norma.materia.tipo
                self.initial['ano_materia'] = norma.materia.ano
                self.initial['numero_materia'] = norma.materia.numero
            return self.initial.copy()
