from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import FormMixin
from vanilla import GenericView

from crud import Crud
from materia.models import Tramitacao
from parlamentares.models import Filiacao

from .forms import (CadastrarComissaoForm, ComposicaoForm,
                    ParticipacaoCadastroForm)
from .models import (CargoComissao, Comissao, Composicao, Participacao,
                     Periodo, TipoComissao)

cargo_crud = Crud(
    CargoComissao, 'cargo_comissao', [

        [_('Período de composição de Comissão'),
         [('nome', 10), ('unico', 2)]],
    ])

periodo_composicao_crud = Crud(
    Periodo, 'periodo_composicao_comissao', [

        [_('Cargo de Comissão'),
         [('data_inicio', 6), ('data_fim', 6)]],
    ])

tipo_comissao_crud = Crud(
    TipoComissao, 'tipo_comissao', [

        [_('Tipo Comissão'),
         [('nome', 9), ('sigla', 3)],
            [('dispositivo_regimental', 9), ('natureza', 3)]],
    ])
comissao_crud = Crud(
    Comissao, 'modulo_comissoes', [

        [_('Dados Básicos'),
         [('nome', 9), ('sigla', 3)],
         [('tipo', 3),
          ('data_criacao', 3),
          ('unidade_deliberativa', 3),
          ('data_extincao', 3)]],

        [_('Dados Complementares'),
         [('local_reuniao', 4),
          ('agenda_reuniao', 4),
          ('telefone_reuniao', 4)],
         [('endereco_secretaria', 4),
          ('telefone_secretaria', 4),
          ('fax_secretaria', 4)],
         [('secretario', 4), ('email', 8)],
         [('finalidade', 12)]],

        [_('Temporária'),
         [('apelido_temp', 8),
          ('data_instalacao_temp', 4)],
         [('data_final_prevista_temp', 4),
          ('data_prorrogada_temp', 4),
          ('data_fim_comissao', 4)]],
    ])


class CadastrarComissaoView(FormMixin, GenericView):

    template_name = "comissoes/cadastrar_comissao.html"

    def get(self, request, *args, **kwargs):
        form = CadastrarComissaoForm()

        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = CadastrarComissaoForm(request.POST, request.FILES)

        if form.is_valid():

            form.save()

            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form})

    def get_success_url(self):
        return reverse('comissao:list')


class ComposicaoView(FormMixin, GenericView):
    template_name = 'comissoes/composicao.html'

    def get(self, request, *args, **kwargs):
        form = ComposicaoForm()

        composicoes = Composicao.objects.filter(
            comissao_id=self.kwargs['pk']).order_by('-periodo')
        participacoes = Participacao.objects.all()

        if composicoes:
            composicao_id = composicoes.first().id
            msg = ''
        else:
            composicao_id = 0
            msg = 'Ainda não há uma composição formada!'
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


class MateriasView(comissao_crud.CrudDetailView):
    template_name = 'comissoes/materias.html'


class ReunioesView(comissao_crud.CrudDetailView):
    template_name = 'comissoes/reunioes.html'


class ComissaoParlamentarIncluirView(FormMixin, GenericView):
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
                        msg = 'Esse cargo já está sendo ocupado!'
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
        return reverse('comissao:composicao', kwargs={'pk': pk})


class ComissaoParlamentarEditView(FormMixin, GenericView):
    template_name = "comissoes/comissao_parlamentar_edit.html"

    def get(self, request, *args, **kwargs):
        participacao_id = kwargs['id']
        participacao = Participacao.objects.get(id=participacao_id)
        comissao = Comissao.objects.get(id=self.kwargs['pk'])
        form = ParticipacaoCadastroForm(
            initial={'parlamentar_id': (Filiacao.objects.get(
                parlamentar__id=participacao.parlamentar.id).id)},
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
        return reverse('comissao:composicao', kwargs={'pk': pk})


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
