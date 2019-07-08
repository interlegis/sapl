from django import forms
from .models import Cronometro, PainelConfig

class CronometroForm(forms.ModelForm):

    class Meta:
        model = Cronometro
        fields = ['tipo', 'duracao_cronometro', 'ativo', 'ordenacao']

    def __init__(self, *args, **kwargs):
        super(CronometroForm, self).__init__(*args, **kwargs)
        self.fields['duracao_cronometro'].widget.attrs['class'] = 'cronometro'
        if not self.instance.ordenacao:
            self.fields['ordenacao'].initial = Cronometro.objects.last().ordenacao + 1


class ConfiguracoesPainelForm(forms.ModelForm):

    class Meta:
        model = PainelConfig
        fields = ['cronometro_ordem', 
                  'disparo_cronometro', 
                  'tempo_disparo_antecedencia',
                  'tempo_disparo_termino',
                  'exibir_nome_casa',
                  'mostrar_votos_antecedencia']

    def __init__(self, *args, **kwargs):
        super(ConfiguracoesPainelForm, self).__init__(*args, **kwargs)
        self.fields['tempo_disparo_antecedencia'].widget.attrs['class'] = 'cronometro'
        self.fields['tempo_disparo_termino'].widget.attrs['class'] = 'cronometro'
