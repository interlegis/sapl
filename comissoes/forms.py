from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
from crispy_layout_mixin import form_actions
from parlamentares.models import Filiacao

from .models import Participacao


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
                _('Cadastro de Parlamentar em Comissão'),
                row1, row2, row3, row4
            ),
            form_actions()
        )
        super(ParticipacaoCadastroForm, self).__init__(*args, **kwargs)
