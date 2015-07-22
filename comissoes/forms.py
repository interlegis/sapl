from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import ugettext as _

from comissoes.models import TipoComissao
from sapl.layout import SaplFormLayout


class TipoComissaoForm(forms.ModelForm):

    class Meta:
        model = TipoComissao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(TipoComissaoForm, self).__init__(*args, **kwargs)
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
