from django import forms

from sapl.comissoes.models import Participacao
from sapl.parlamentares.models import Parlamentar, Legislatura, Mandato


class ParticipacaoForm(forms.ModelForm):

    # composicao = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = Participacao
        # exclude = []
        exclude = ['composicao']

    def __init__(self, user=None, **kwargs):
        super(ParticipacaoForm, self).__init__(**kwargs)
        legislatura = Legislatura.objects.order_by('-data_inicio').first()
        parlamentares = Mandato.objects.filter(legislatura=legislatura,
                                               parlamentar__ativo=True
                                               ).prefetch_related('parlamentar').\
                                               values_list('parlamentar',
                                                           flat=True)
        qs = Parlamentar.objects.filter(id__in=parlamentares).distinct()
        self.fields['parlamentar'].queryset = qs

    def clean(self):
        super(ParticipacaoForm, self).clean()

        return self.cleaned_data
