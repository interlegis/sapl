from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, ListView

import crud.base
import crud.masterdetail
from crud.base import Crud
from crud.masterdetail import MasterDetailCrud
from materia.models import Tramitacao
from parlamentares.models import Filiacao

from .forms import ComposicaoForm, ParticipacaoCadastroForm
from .models import (CargoComissao, Comissao, Composicao, Participacao,
                     Periodo, TipoComissao)

CargoCrud = Crud.build(CargoComissao, 'cargo_comissao')
PeriodoComposicaoCrud = Crud.build(Periodo, 'periodo_composicao_comissao')
TipoComissaoCrud = Crud.build(TipoComissao, 'tipo_comissao')


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


class ComissaoParlamentarIncluirView(FormView):
    template_name = "comissoes/comissao_parlamentar.html"

    def get(self, request, *args, **kwargs):
        form = ParticipacaoCadastroForm()
        comissao = Comissao.objects.get(id=self.kwargs['pk'])
        return self.render_to_response({'form': form,
                                        'composicao_id': self.kwargs['id'],
                                        'comissao': comissao})

    def post(self, request, *args, **kwargs):
        composicao = Composicao.objects.get(id=self.kwargs['id'])
        form = ParticipacaoCadastroForm(request.POST)
        comissao = Comissao.objects.get(id=self.kwargs['pk'])

        if form.is_valid():
            cargo = form.cleaned_data['cargo']
            if cargo.nome == 'Presidente':
                for p in Participacao.objects.filter(composicao=composicao):
                    if p.cargo.nome == 'Presidente':
                        msg = _('Esse cargo já está sendo ocupado!')
                        messages.add_message(request, messages.INFO, msg)
                        return self.render_to_response(
                            {'form': form,
                             'composicao_id': self.kwargs['id'],
                             'comissao': comissao})
                    else:
                        # Pensar em forma melhor para não duplicar código
                        participacao = form.save(commit=False)
                        participacao.composicao = composicao
                        participacao.parlamentar = (
                            form.cleaned_data['parlamentar_id'].parlamentar)

                        participacao.save()
            else:
                participacao = form.save(commit=False)
                participacao.composicao = composicao
                participacao.parlamentar = (
                    form.cleaned_data['parlamentar_id'].parlamentar)

                participacao.save()
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'composicao_id': self.kwargs['id'],
                 'comissao': comissao})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('comissoes:composicao', kwargs={'pk': pk})


class ComissaoParlamentarEditView(FormView):
    template_name = "comissoes/comissao_parlamentar_edit.html"

    def get(self, request, *args, **kwargs):
        participacao_id = kwargs['id']
        participacao = Participacao.objects.get(id=participacao_id)
        comissao = Comissao.objects.get(id=self.kwargs['pk'])
        id_parlamentar = Filiacao.objects.filter(
            parlamentar__id=participacao.parlamentar.id).order_by('data')
        id_parlamentar = id_parlamentar.last().id
        form = ParticipacaoCadastroForm(
            initial={'parlamentar_id': id_parlamentar},
            instance=participacao)
        return self.render_to_response({'form': form,
                                        'comissao': comissao,
                                        'composicao_id': self.kwargs['id']})

    def post(self, request, *args, **kwargs):
        form = ParticipacaoCadastroForm(request.POST)
        if form.is_valid():
            participacao = ParticipacaoCadastroForm(
                request.POST,
                request.FILES,
                instance=Participacao.objects.get(id=kwargs['id'])
            ).save(commit=False)

            participacao.composicao = Composicao.objects.get(
                id=kwargs['cd'])
            participacao.parlamentar = (
                form.cleaned_data['parlamentar_id'].parlamentar)
            participacao.save()
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'composicao_id': self.kwargs['id']})

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('comissoes:composicao', kwargs={'pk': pk})


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
