from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, FormView, ListView

from crud.base import Crud
from materia.models import Tramitacao
from parlamentares.models import Filiacao

from .forms import (CadastrarComissaoForm, ComposicaoForm,
                    ParticipacaoCadastroForm)
from .models import (CargoComissao, Comissao, Composicao, Participacao,
                     Periodo, TipoComissao)

CargoCrud = Crud.build(CargoComissao, 'cargo_comissao')
PeriodoComposicaoCrud = Crud.build(Periodo, 'periodo_composicao_comissao')
TipoComissaoCrud = Crud.build(TipoComissao, 'tipo_comissao')
ComissaoCrud = Crud.build(Comissao, 'modulo_comissoes')


class CadastrarComissaoView(CreateView):
    template_name = "comissoes/cadastrar_comissao.html"
    form_class = CadastrarComissaoForm
    success_url = reverse_lazy('comissoes:comissao_list')


class ComposicaoView(FormView):
    template_name = 'comissoes/composicao.html'

    def get(self, request, *args, **kwargs):
        form = ComposicaoForm()

        composicoes = Composicao.objects.filter(
            comissao_id=self.kwargs['pk']).order_by('-periodo')
        participacoes = Participacao.objects.all().order_by('parlamentar')

        if composicoes:
            composicao_id = composicoes.first().id
            msg = ''
        else:
            composicao_id = 0
            msg = _('Ainda não há uma composição formada!')
            messages.add_message(request, messages.INFO, msg)

        return self.render_to_response({
            'participacoes': participacoes,
            'composicoes': composicoes,
            'composicao_id': composicao_id,
            'form': form,
            'pk': self.kwargs['pk'],
            'object': Comissao.objects.get(id=self.kwargs['pk'])})

    def post(self, request, *args, **kwargs):
        form = ComposicaoForm(request.POST)

        composicoes = Composicao.objects.filter(
            comissao_id=self.kwargs['pk']).order_by('-periodo')
        participacoes = Participacao.objects.all()

        return self.render_to_response({
            'participacoes': participacoes,
            'composicoes': composicoes,
            'composicao_id': int(form.data['periodo']),
            'form': form,
            'pk': self.kwargs['pk'],
            'object': Comissao.objects.get(id=self.kwargs['pk'])})


class MateriasView(ComissaoCrud.CrudDetailView):
    template_name = 'comissoes/materias.html'


class ReunioesView(ComissaoCrud.CrudDetailView):
    template_name = 'comissoes/reunioes.html'


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
