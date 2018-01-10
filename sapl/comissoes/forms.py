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
        eligible = self.verifica()
        result = list(set(qs) & set(eligible))
        if not cmp(result, eligible): # se igual a 0 significa que o qs e o eli são iguais!
            self.fields['parlamentar'].queryset = qs
        else:
            ids = [e.id for e in eligible]
            qs = Parlamentar.objects.filter(id__in=ids)
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

        # if self.instance:
        return self.cleaned_data

    def verifica(self):
        composicao = Composicao.objects.get(id=self.initial['parent_pk'])
        participantes = composicao.participacao_set.all()
        participantes_id = [p.parlamentar.id for p in participantes]
        parlamentares = Parlamentar.objects.all().exclude(id__in=participantes_id).order_by('nome_completo')
        parlamentares = [p for p in parlamentares if p.ativo]

        lista = []

        for p in parlamentares:
            mandatos = p.mandato_set.all()
            for m in mandatos:
                data_inicio = m.data_inicio_mandato
                data_fim = m.data_fim_mandato
                comp_data_inicio = composicao.periodo.data_inicio
                comp_data_fim = composicao.periodo.data_fim
                if (data_fim and data_fim >= comp_data_inicio)\
                    or (data_inicio >= comp_data_inicio and data_inicio <= comp_data_fim)\
                    or (data_fim is None and data_inicio <= comp_data_inicio):
                    lista.append(p)

        lista = list(set(lista))

        return lista
