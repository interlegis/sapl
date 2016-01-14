from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Fieldset, Layout, Submit
from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormMixin
from vanilla import GenericView

import sapl
from parlamentares.models import Filiacao
from sapl.crud import build_crud

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


class CadastrarComissaoForm(ModelForm):

    class Meta:

        model = Comissao
        fields = ['nome',
                  'tipo',
                  'sigla',
                  'data_criacao',
                  'data_extincao',
                  'unidade_deliberativa',

                  'local_reuniao',
                  'agenda_reuniao',
                  'telefone_reuniao',
                  'endereco_secretaria',
                  'telefone_secretaria',
                  'fax_secretaria',
                  'secretario',
                  'email',
                  'finalidade',

                  'apelido_temp',
                  'data_instalacao_temp',
                  'data_final_prevista_temp',
                  'data_prorrogada_temp',
                  'data_fim_comissao']

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('nome', 8),
             ('sigla', 4)])

        row2 = sapl.layout.to_row(
            [('tipo', 3),
             ('data_criacao', 3),
             ('unidade_deliberativa', 3),
             ('data_extincao', 3)])

        row3 = sapl.layout.to_row(
            [('local_reuniao', 4),
             ('agenda_reuniao', 4),
             ('telefone_reuniao', 4)])

        row4 = sapl.layout.to_row(
            [('endereco_secretaria', 4),
             ('telefone_secretaria', 4),
             ('fax_secretaria', 4)])

        row5 = sapl.layout.to_row(
            [('secretario', 6),
             ('email', 6)])

        row6 = sapl.layout.to_row(
            [('finalidade', 12)])

        row7 = sapl.layout.to_row(
            [('apelido_temp', 9),
             ('data_instalacao_temp', 3)])

        row8 = sapl.layout.to_row(
            [('data_final_prevista_temp', 4),
             ('data_prorrogada_temp', 4),
             ('data_fim_comissao', 4)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Cadastrar Comissão',
                Fieldset(
                    'Dados Básicos',
                    row1,
                    row2
                ),
                Fieldset(
                    'Dados Complementares',
                    row3,
                    row4,
                    row5,
                    row6
                ),
                Fieldset(
                    'Temporária',
                    row7,
                    row8
                ),
                ButtonHolder(
                    Submit('submit', 'Salvar',
                           css_class='button primary')
                )
            )
        )
        super(CadastrarComissaoForm, self).__init__(*args, **kwargs)


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


class ComposicaoForm(forms.Form):
    periodo = forms.CharField()


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
            msg = 'Ainda não há composição nessa comissão.'

        return self.render_to_response({
            'participacoes': participacoes,
            'composicoes': composicoes,
            'composicao_id': composicao_id,
            'form': form,
            'pk': self.kwargs['pk'],
            'comissao': Comissao.objects.get(id=self.kwargs['pk']),
            'error': msg})

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
            'comissao': Comissao.objects.get(id=self.kwargs['pk'])})


class MateriasView(comissao_crud.CrudDetailView):
    template_name = 'comissoes/materias.html'


class ReunioesView(comissao_crud.CrudDetailView):
    template_name = 'comissoes/reunioes.html'


class ParticipacaoCadastroForm(ModelForm):

    YES_OR_NO = (
        (True, 'Sim'),
        (False, 'Não')
    )

    parlamentar_id = forms.ModelChoiceField(
        label='Parlamentar',
        required=True,
        queryset=Filiacao.objects.filter(
            data_desfiliacao__isnull=True, parlamentar__ativo=True).order_by(
            'parlamentar__nome_parlamentar'),
        empty_label='Selecione',
    )

    data_designacao = forms.DateField(label=u'Data Designação',
                                      input_formats=['%d/%m/%Y'],
                                      required=True,
                                      widget=forms.DateInput(
                                          format='%d/%m/%Y'))

    data_desligamento = forms.DateField(label=u'Data Desligamento',
                                        input_formats=['%d/%m/%Y'],
                                        required=False,
                                        widget=forms.DateInput(
                                            format='%d/%m/%Y'))

    class Meta:
        model = Participacao
        fields = ['parlamentar_id',
                  'cargo',
                  'titular',
                  'data_designacao',
                  'data_desligamento',
                  'motivo_desligamento',
                  'observacao']

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()

        row1 = sapl.layout.to_row(
            [('parlamentar_id', 4),
             ('cargo', 4),
             ('titular', 4)])

        row2 = sapl.layout.to_row(
            [('data_designacao', 6),
             ('data_desligamento', 6)])

        row3 = sapl.layout.to_row(
            [('motivo_desligamento', 12)])

        row4 = sapl.layout.to_row(
            [('observacao', 12)])

        self.helper.layout = Layout(
            Fieldset(
                'Formulário de Cadastro',
                row1, row2, row3, row4
            ),
            ButtonHolder(
                Submit('submit', 'Salvar',
                       css_class='button primary')
            )
        )
        super(ParticipacaoCadastroForm, self).__init__(*args, **kwargs)


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
            initial={'parlamentar_id': participacao.parlamentar.id},
            instance=participacao)
        return self.render_to_response({'form': form,
                                        'comissao': comissao,
                                        'composicao_id': self.kwargs['id']})
