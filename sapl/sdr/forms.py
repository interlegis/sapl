import logging

from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from sapl.sdr.models import DeliberacaoRemota
from sapl.sessao.models import SessaoPlenaria


class DeliberacaoRemotaForm(ModelForm):
    logger = logging.getLogger(__name__)

    sessao_plenaria = forms.ModelChoiceField(
        label=_('Sessão Plenária'),
        required=False,
        empty_label='Selecione',
        queryset=SessaoPlenaria.objects.filter(
            finalizada=False
        ).order_by("-data_inicio", "-hora_inicio")
    )

    class Meta:
        model = DeliberacaoRemota
        exclude = ['chat_id']

        widgets = {
            'created_by': forms.HiddenInput(),
            'inicio': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()

        if not self.is_valid():
            return self.cleaned_data

        if not self.instance.finalizada: 
            if cleaned_data['finalizada']:
                cleaned_data['termino'] = timezone.now()
        else:
            if not cleaned_data['finalizada']:
                cleaned_data['termino'] = None
            else: 
                cleaned_data['termino'] = self.instance.termino

        return cleaned_data
