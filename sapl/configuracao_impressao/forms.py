from django import forms
from .models import ConfiguracaoImpressao


class ConfiguracaoImpressaoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoImpressao
        fields = '__all__'