from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import ugettext as _

from comissoes.models import Comissao, TipoComissao
from sapl.layout import SaplFormLayout


class TipoComissaoForm(forms.ModelForm):

    class Meta:
        model = TipoComissao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(ComissaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Tipo Comissão'),
             [('nome', 3),
              ('nome', 3),
              ('sigla', 2),
              ('dispositivo_regimental', 2),
              ('natureza', 2)],
             [('nome', 6), ('sigla', 6)],
             [('dispositivo_regimental', 6), ('natureza', 6)]],

        )


class ComissaoForm(forms.ModelForm):

    class Meta:
        model = Comissao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(ComissaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

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
             [('apelido_temp', 8), ('data_instalacao_temp', 4)],
             [('data_final_prevista_temp', 4),
              ('data_prorrogada_temp', 4),
              ('data_fim_comissao', 4)]],
        )
