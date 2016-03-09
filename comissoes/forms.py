from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
from crispy_layout_mixin import form_actions
from parlamentares.models import Filiacao

from .models import Comissao, Participacao


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

        row1 = crispy_layout_mixin.to_row(
            [('nome', 8),
             ('sigla', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('tipo', 3),
             ('data_criacao', 3),
             ('unidade_deliberativa', 3),
             ('data_extincao', 3)])

        row3 = crispy_layout_mixin.to_row(
            [('local_reuniao', 4),
             ('agenda_reuniao', 4),
             ('telefone_reuniao', 4)])

        row4 = crispy_layout_mixin.to_row(
            [('endereco_secretaria', 4),
             ('telefone_secretaria', 4),
             ('fax_secretaria', 4)])

        row5 = crispy_layout_mixin.to_row(
            [('secretario', 6),
             ('email', 6)])

        row6 = crispy_layout_mixin.to_row(
            [('finalidade', 12)])

        row7 = crispy_layout_mixin.to_row(
            [('apelido_temp', 9),
             ('data_instalacao_temp', 3)])

        row8 = crispy_layout_mixin.to_row(
            [('data_final_prevista_temp', 4),
             ('data_prorrogada_temp', 4),
             ('data_fim_comissao', 4)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Cadastrar Comissão'),
                Fieldset(
                    _('Dados Básicos'),
                    row1,
                    row2
                ),
                Fieldset(
                    _('Dados Complementares'),
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
                form_actions()
            )
        )
        super(CadastrarComissaoForm, self).__init__(*args, **kwargs)


class ComposicaoForm(forms.Form):
    periodo = forms.CharField()


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

    class Meta:
        model = Participacao
        fields = ['parlamentar_id',
                  'cargo',
                  'titular',
                  'data_designacao',
                  'data_desligamento',
                  'motivo_desligamento',
                  'observacao']

        widgets = {
            'data_designacao': forms.DateInput(format='%d/%m/%Y'),
            'data_desligamento': forms.DateInput(format='%d/%m/%Y'),
        }

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()

        row1 = crispy_layout_mixin.to_row(
            [('parlamentar_id', 4),
             ('cargo', 4),
             ('titular', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('data_designacao', 6),
             ('data_desligamento', 6)])

        row3 = crispy_layout_mixin.to_row(
            [('motivo_desligamento', 12)])

        row4 = crispy_layout_mixin.to_row(
            [('observacao', 12)])

        self.helper.layout = Layout(
            Fieldset(
                _('Formulário de Cadastro'),
                row1, row2, row3, row4
            ),
            form_actions()
        )
        super(ParticipacaoCadastroForm, self).__init__(*args, **kwargs)
