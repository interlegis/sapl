from django import forms
from .models import Cronometro

class CronometroForm(forms.ModelForm):

    class Meta:
        model = Cronometro
        fields = ['tipo', 'duracao_cronometro', 'ativo', 'ordenacao']

    def __init__(self, *args, **kwargs):
        super(CronometroForm, self).__init__(*args, **kwargs)
        self.fields['duracao_cronometro'].widget.attrs['class'] = 'cronometro'
        if not self.instance.ordenacao:
            self.fields['ordenacao'].initial = Cronometro.objects.last().ordenacao + 1