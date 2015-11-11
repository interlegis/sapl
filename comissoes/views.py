from django import forms
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import FormMixin
from sapl.crud import build_crud
from vanilla import GenericView

from .models import (CargoComissao, Comissao, Composicao, Participacao,
                     Periodo, TipoComissao)

cargo_crud = build_crud(
    CargoComissao, 'cargo_comissao', [

        [_('Período de composição de Comissão'),
         [('nome', 10), ('unico', 2)]],
    ])

periodo_composicao_crud = build_crud(
    Periodo, 'periodo_composicao_comissao', [

        [_('Cargo de Comissão'),
         [('data_inicio', 6), ('data_fim', 6)]],
    ])

tipo_comissao_crud = build_crud(
    TipoComissao, 'tipo_comissao', [

        [_('Tipo Comissão'),
         [('nome', 9), ('sigla', 3)],
            [('dispositivo_regimental', 9), ('natureza', 3)]],
    ])

comissao_crud = build_crud(
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


class ComposicaoForm(forms.Form):
    periodo = forms.CharField()


class ComposicaoView(FormMixin, GenericView):
    template_name = 'comissoes/composicao.html'

    def get(self, request, *args, **kwargs):
        form = ComposicaoForm()

        composicoes = Composicao.objects.filter(
            comissao_id=self.kwargs['pk']).order_by('-periodo')
        participacoes = Participacao.objects.all()

        return self.render_to_response({
            'participacoes': participacoes,
            'composicoes': composicoes,
            'composicao_id': composicoes.first().id,
            'form': form})

    def post(self, request, *args, **kwargs):
        form = ComposicaoForm(request.POST)

        composicoes = Composicao.objects.filter(
            comissao_id=self.kwargs['pk']).order_by('-periodo')
        participacoes = Participacao.objects.all()

        return self.render_to_response({
            'participacoes': participacoes,
            'composicoes': composicoes,
            'composicao_id': int(form.data['periodo']),
            'form': form})


class MateriasView(comissao_crud.CrudDetailView):
    template_name = 'comissoes/materias.html'


class ReunioesView(comissao_crud.CrudDetailView):
    template_name = 'comissoes/reunioes.html'


class ComissaoParlamentarIncluirView(comissao_crud.CrudDetailView):
    template_name = "comissoes/comissao_parlamentar.html"
