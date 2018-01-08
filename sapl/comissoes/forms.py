from django.db.models import Q
from django import forms

from sapl.comissoes.models import Participacao, Composicao
from sapl.parlamentares.models import Parlamentar, Legislatura, Mandato


class ParticipacaoForm(forms.ModelForm):

    parent_pk = forms.CharField(required=False) # widget=forms.HiddenInput())

    class Meta:
        model = Participacao
        # includes = ['parlamentar', 'cargo', 'titular', 'data_designacao', 'data_desligamento', 'data_']
        # exclude = []
        exclude = ['composicao']

    def __init__(self, user=None, **kwargs):
        super(ParticipacaoForm, self).__init__(**kwargs)

        if self.instance:
            comissao = kwargs['initial']
            comissao_pk = int(comissao['parent_pk'])
            composicao = Composicao.objects.get(id=comissao_pk)
            participantes = composicao.participacao_set.all()
            id_part = [p.parlamentar.id for p in participantes]
        else:
            id_part = []

        qs = self.create_participacao()

        parlamentares = Mandato.objects.filter(qs,
                                               parlamentar__ativo=True
                                               ).prefetch_related('parlamentar').\
                                               values_list('parlamentar',
                                                           flat=True).distinct()

        qs = Parlamentar.objects.filter(id__in=parlamentares).distinct().\
        exclude(id__in=id_part)

        self.fields['parlamentar'].queryset = qs

    def create_participacao(self):
        composicao = Composicao.objects.get(id=self.initial['parent_pk'])
        data_inicio_comissao = composicao.periodo.data_inicio
        data_fim_comissao = composicao.periodo.data_fim
        q1 = Q(data_fim_mandato__isnull=False,
               data_fim_mandato__gte=data_inicio_comissao)
        q2 = Q(data_inicio_mandato__gte=data_inicio_comissao) \
             & Q(data_inicio_mandato__lte=data_fim_comissao)
        q3 = Q(data_fim_mandato__isnull=True,
               data_inicio_mandato__lte=data_inicio_comissao)
        qs = q1 | q2 | q3
        return qs

    def clean(self):
        super(ParticipacaoForm, self).clean()
        # import ipdb; ipdb.set_trace()

        # if self.instance:
        return self.cleaned_data
