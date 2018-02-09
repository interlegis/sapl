from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from sapl.base.models import Autor, TipoAutor
from sapl.comissoes.models import Comissao, Composicao, Participacao
from sapl.parlamentares.models import Legislatura, Mandato, Parlamentar


class ParticipacaoCreateForm(forms.ModelForm):

    parent_pk = forms.CharField(required=False)  # widget=forms.HiddenInput())

    class Meta:
        model = Participacao
        exclude = ['composicao']

    def __init__(self, user=None, **kwargs):
        super(ParticipacaoCreateForm, self).__init__(**kwargs)

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
        if not cmp(result, eligible):  # se igual a 0 significa que o qs e o eli são iguais!
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
        super(ParticipacaoCreateForm, self).clean()
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


class ParticipacaoEditForm(forms.ModelForm):

    parent_pk = forms.CharField(required=False)  # widget=forms.HiddenInput())
    nome_parlamentar = forms.CharField(required=False, label='Parlamentar')

    class Meta:
        model = Participacao
        fields = ['nome_parlamentar', 'parlamentar', 'cargo', 'titular',
                  'data_designacao', 'data_desligamento',
                  'motivo_desligamento', 'observacao']
        widgets = {
            'parlamentar': forms.HiddenInput(),
        }

    def __init__(self, user=None, **kwargs):
        super(ParticipacaoEditForm, self).__init__(**kwargs)
        self.initial['nome_parlamentar'] = Parlamentar.objects.get(
            id=self.initial['parlamentar']).nome_parlamentar
        self.fields['nome_parlamentar'].widget.attrs['disabled'] = 'disabled'


class ComissaoForm(forms.ModelForm):

    class Meta:
        model = Comissao
        fields = '__all__'

    def clean(self):
        super(ComissaoForm, self).clean()

        if self.cleaned_data['data_extincao']:
            if (self.cleaned_data['data_extincao'] <
                    self.cleaned_data['data_criacao']):
                msg = _('Data de extinção não pode ser menor que a de criação')
                raise ValidationError(msg)
        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        comissao = super(ComissaoForm, self).save(commit)
        content_type = ContentType.objects.get_for_model(Comissao)
        object_id = comissao.pk
        tipo = TipoAutor.objects.get(descricao__icontains='Comiss')
        nome = comissao.sigla + ' - ' + comissao.nome
        Autor.objects.create(
            content_type=content_type,
            object_id=object_id,
            tipo=tipo,
            nome=nome
        )
        return comissao
