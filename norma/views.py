from datetime import datetime
from re import sub

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, ListView
from django.views.generic.edit import FormMixin
from vanilla.views import GenericView

from compilacao.views import IntegracaoTaView
from crud import Crud, make_pagination
from materia.models import MateriaLegislativa, TipoMateriaLegislativa

from .forms import NormaJuridicaForm, NormaJuridicaPesquisaForm
from .models import (AssuntoNorma, LegislacaoCitada, NormaJuridica,
                     TipoNormaJuridica)

assunto_norma_crud = Crud(AssuntoNorma, 'assunto_norma_juridica')
tipo_norma_crud = Crud(TipoNormaJuridica, 'tipo_norma_juridica')
norma_crud = Crud(NormaJuridica, '')
norma_temporario_crud = Crud(NormaJuridica, 'normajuridica')
legislacao_citada_crud = Crud(LegislacaoCitada, '')


class NormaPesquisaView(GenericView):
    template_name = "norma/pesquisa.html"

    def get_success_url(self):
        return reverse('normajuridica:norma_pesquisa')

    def get(self, request, *args, **kwargs):
        form = NormaJuridicaPesquisaForm()
        return self.render_to_response({'form': form})

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
        if form.data['publicação_inicial'] and form.data['publicação_final']:
            kwargs['publicação_inicial'] = form.data['publicação_inicial']
            kwargs['publicação_final'] = form.data['publicação_final']

        request.session['kwargs'] = kwargs
        return redirect('list_pesquisa_norma')


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
            publicação_inicial = datetime.strptime(
                kwargs['publicação_inicial'],
                '%d/%m/%Y').strftime('%Y-%m-%d')
            publicação_final = datetime.strptime(
                kwargs['publicação_final'],
                '%d/%m/%Y').strftime('%Y-%m-%d')

            normas = normas.filter(
                data__range=(periodo_inicial, periodo_final),
                data_publicacao__range=(publicação_inicial, publicação_final))

        if 'periodo_inicial' in kwargs:
            inicial = datetime.strptime(kwargs['periodo_inicial'],
                                        '%d/%m/%Y').strftime('%Y-%m-%d')
            final = datetime.strptime(kwargs['periodo_inicial'],
                                      '%d/%m/%Y').strftime('%Y-%m-%d')

            normas = normas.filter(data__range=(inicial, final))

        if 'publicação_inicial' in kwargs:
            inicial = datetime.strptime(kwargs['publicação_inicial'],
                                        '%d/%m/%Y').strftime('%Y-%m-%d')
            final = datetime.strptime(kwargs['publicação_final'],
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


class NormaIncluirView(CreateView):
    template_name = "norma/normajuridica_incluir.html"
    form_class = NormaJuridicaForm

    def get_success_url(self):
        return reverse('normajuridica:list')

    def get(self, request, *args, **kwargs):
        form = NormaJuridicaForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            norma = form.save(commit=False)

            if form.cleaned_data['tipo_materia']:
                try:
                    materia = MateriaLegislativa.objects.get(
                        tipo_id=form.cleaned_data['tipo_materia'],
                        numero=form.cleaned_data['numero_materia'],
                        ano=form.cleaned_data['ano_materia'])
                except ObjectDoesNotExist:
                    msg = 'Matéria adicionada não existe!'
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response({'form': form})
                else:
                    norma.materia = materia
            norma.timestamp = datetime.now()
            norma.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response({'form': form})


class NormaEditView(CreateView):
    template_name = "norma/normajuridica_incluir.html"
    form_class = NormaJuridicaForm

    def get(self, request, *args, **kwargs):
        norma = NormaJuridica.objects.get(id=self.kwargs['pk'])
        form = NormaJuridicaForm(instance=norma)
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        norma = NormaJuridica.objects.get(id=self.kwargs['pk'])
        form = NormaJuridicaForm(instance=norma, data=request.POST)

        if form.is_valid():
            if form.data['tipo_materia']:
                try:
                    materia = MateriaLegislativa.objects.get(
                        tipo_id=form.data['tipo_materia'],
                        numero=form.data['numero_materia'],
                        ano=form.data['ano_materia'])
                except ObjectDoesNotExist:
                    msg = 'Matéria adicionada não existe!'
                    messages.add_message(request, messages.INFO, msg)
                    return self.render_to_response({'form': form})
                else:
                    norma.materia = materia
            norma = form.save(commit=False)
            norma.timestamp = datetime.now()
            norma.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response({'form': form})

    def get_success_url(self):
        return reverse('normajuridica:list')


class NormaTaView(IntegracaoTaView):
    model = NormaJuridica
    model_type_foreignkey = TipoNormaJuridica
