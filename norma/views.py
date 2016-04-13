from datetime import datetime

from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic import CreateView, FormView, ListView, UpdateView

import crud.base
from compilacao.views import IntegracaoTaView
from crud.base import Crud, make_pagination
from materia.models import MateriaLegislativa

from .forms import NormaJuridicaForm, NormaJuridicaPesquisaForm
from .models import (AssuntoNorma, LegislacaoCitada, NormaJuridica,
                     TipoNormaJuridica)

AssuntoNormaCrud = Crud.build(AssuntoNorma, 'assunto_norma_juridica')
TipoNormaCrud = Crud.build(TipoNormaJuridica, 'tipo_norma_juridica')
NormaTemporarioCrud = Crud.build(NormaJuridica, 'norma')
LegislacaoCitadaCrud = Crud.build(LegislacaoCitada, '')


class NormaCrud(Crud):
    model = NormaJuridica
    help_path = 'norma_juridica'

    class UpdateView(crud.base.CrudUpdateView):
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

    class CreateView(crud.base.CrudCreateView):
        form_class = NormaJuridicaForm

        @property
        def layout_key(self):
            return 'NormaJuridicaCreate'

    class BaseMixin(crud.base.BaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'ementa']


class NormaPesquisaView(FormView):
    template_name = "norma/pesquisa.html"
    success_url = "norma:norma_pesquisa"
    form_class = NormaJuridicaPesquisaForm

    def post(self, request, *args, **kwargs):
        form = NormaJuridicaPesquisaForm(request.POST)

        if form.data['tipo']:
            kwargs['tipo'] = form.data['tipo']
        if form.data['numero']:
            kwargs['numero'] = form.data['numero']
        if form.data['ano']:
            kwargs['ano'] = form.data['ano']
        if form.data['periodo_inicial'] and form.data['periodo_final']:
            kwargs['periodo_inicial'] = form.data['periodo_inicial']
            kwargs['periodo_final'] = form.data['periodo_final']
        if form.data['publicacao_inicial'] and form.data['publicacao_final']:
            kwargs['publicacao_inicial'] = form.data['publicacao_inicial']
            kwargs['publicacao_final'] = form.data['publicacao_final']

        request.session['kwargs'] = kwargs
        return redirect('norma:list_pesquisa_norma')


class PesquisaNormaListView(ListView):
    template_name = 'norma/list_pesquisa.html'
    model = NormaJuridica
    paginate_by = 10

    def get_queryset(self):
        kwargs = self.request.session['kwargs']
        normas = NormaJuridica.objects.all().order_by('-ano', '-numero')

        if 'periodo_inicial' and 'publicacao_inicial' in kwargs:
            periodo_inicial = datetime.strptime(
                kwargs['periodo_inicial'],
                '%d/%m/%Y').strftime('%Y-%m-%d')
            periodo_final = datetime.strptime(
                kwargs['periodo_final'],
                '%d/%m/%Y').strftime('%Y-%m-%d')
            publicacao_inicial = datetime.strptime(
                kwargs['publicacao_inicial'],
                '%d/%m/%Y').strftime('%Y-%m-%d')
            publicacao_final = datetime.strptime(
                kwargs['publicacao_final'],
                '%d/%m/%Y').strftime('%Y-%m-%d')

            normas = normas.filter(
                data__range=(periodo_inicial, periodo_final),
                data_publicacao__range=(publicacao_inicial, publicacao_final))

        if 'periodo_inicial' in kwargs:
            inicial = datetime.strptime(kwargs['periodo_inicial'],
                                        '%d/%m/%Y').strftime('%Y-%m-%d')
            final = datetime.strptime(kwargs['periodo_inicial'],
                                      '%d/%m/%Y').strftime('%Y-%m-%d')

            normas = normas.filter(data__range=(inicial, final))

        if 'publicacao_inicial' in kwargs:
            inicial = datetime.strptime(kwargs['publicacao_inicial'],
                                        '%d/%m/%Y').strftime('%Y-%m-%d')
            final = datetime.strptime(kwargs['publicacao_final'],
                                      '%d/%m/%Y').strftime('%Y-%m-%d')

            normas = normas.filter(data_publicacao__range=(inicial, final))
        if 'tipo' in kwargs:
            normas = normas.filter(tipo=kwargs['tipo'])

        if 'numero' in kwargs:
            normas = normas.filter(numero=kwargs['numero'])

        if 'ano' in kwargs:
            normas = normas.filter(ano=kwargs['ano'])

        return normas

    def get_context_data(self, **kwargs):
        context = super(PesquisaNormaListView, self).get_context_data(
            **kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        return context


class NormaTaView(IntegracaoTaView):
    model = NormaJuridica
    model_type_foreignkey = TipoNormaJuridica
