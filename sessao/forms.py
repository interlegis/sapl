from datetime import datetime

import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
from crispy_layout_mixin import form_actions
from materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.utils import RANGE_DIAS_MES, RANGE_MESES

from .models import ExpedienteMateria, SessaoPlenaria


def pega_anos():
    try:
        anos_list = SessaoPlenaria.objects.all().dates('data_inicio', 'year')
        anos = [(k.year, k.year) for k in anos_list]
        return anos
    except:
        return []

ANO_CHOICES = [('', '---------')] + pega_anos()
MES_CHOICES = [('', '---------')] + RANGE_MESES
DIA_CHOICES = [('', '---------')] + RANGE_DIAS_MES


class ExpedienteMateriaForm(ModelForm):

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo Matéria'),
        required=True,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero_materia = forms.CharField(
        label='Número Matéria', required=True)

    ano_materia = forms.CharField(
        label='Ano Matéria', required=True)

    data_ordem = forms.CharField(
        initial=datetime.now().strftime('%d/%m/%Y'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = ExpedienteMateria
        fields = ['data_ordem', 'numero_ordem', 'tipo_materia', 'observacao',
                  'numero_materia', 'ano_materia', 'tipo_votacao']

    def clean_data_ordem(self):
        return datetime.now()

    def clean(self):
        cleaned_data = self.cleaned_data
        try:
            materia = MateriaLegislativa.objects.get(
                numero=self.cleaned_data['numero_materia'],
                ano=self.cleaned_data['ano_materia'],
                tipo=self.cleaned_data['tipo_materia'])
        except ObjectDoesNotExist:
            msg = _('A matéria a ser inclusa não existe no cadastro'
                    ' de matérias legislativas.')
            raise ValidationError(msg)
        else:
            cleaned_data['materia'] = materia

        return cleaned_data

    def save(self, commit=False):
        expediente = super(ExpedienteMateriaForm, self).save(commit)
        expediente.materia = self.cleaned_data['materia']
        expediente.save()
        return expediente


class PresencaForm(forms.Form):
    presenca = forms.CharField(required=False, initial=False)
    parlamentar = forms.CharField(required=False, max_length=20)


class VotacaoNominalForm(forms.Form):
    pass


class ListMateriaForm(forms.Form):
    error_message = forms.CharField(required=False, label='votacao_aberta')


class MateriaOrdemDiaForm(forms.Form):
    data_sessao = forms.CharField(required=True, label=_('Data da Sessão'))
    numero_ordem = forms.IntegerField(required=True, label=_('Número Ordem'))
    tipo_votacao = forms.IntegerField(required=True, label=_('Tipo Votação'))
    tipo_sessao = forms.IntegerField(required=True, label=_('Tipo da Sessão'))
    ano_materia = forms.IntegerField(required=True, label=_('Ano Matéria'))
    numero_materia = forms.IntegerField(required=True,
                                        label=_('Número Matéria'))
    tipo_materia = forms.IntegerField(required=True, label=_('Tipo Matéria'))
    observacao = forms.CharField(required=False, label=_('Ementa'))
    error_message = forms.CharField(required=False, label=_('Matéria'))


class MesaForm(forms.Form):
    parlamentar = forms.IntegerField(required=True)
    cargo = forms.IntegerField(required=True)


class ExpedienteForm(forms.Form):
    conteudo = forms.CharField(required=False, widget=forms.Textarea)


class VotacaoForm(forms.Form):
    votos_sim = forms.CharField(required=True, label='Sim')
    votos_nao = forms.CharField(required=True, label='Não')
    abstencoes = forms.CharField(required=True, label='Abstenções')
    total_votos = forms.CharField(required=False, label='total')


class VotacaoEditForm(forms.Form):
    pass


class SessaoPlenariaFilterSet(django_filters.FilterSet):
    data_inicio__year = django_filters.ChoiceFilter(required=False,
                                                    label=u'Ano',
                                                    choices=ANO_CHOICES)
    data_inicio__month = django_filters.ChoiceFilter(required=False,
                                                     label=u'Mês',
                                                     choices=MES_CHOICES)
    data_inicio__day = django_filters.ChoiceFilter(required=False,
                                                   label=u'Dia',
                                                   choices=DIA_CHOICES)

    class Meta:
        model = SessaoPlenaria
        fields = ['tipo']

    def __init__(self, *args, **kwargs):
        super(SessaoPlenariaFilterSet, self).__init__(*args, **kwargs)

        row1 = crispy_layout_mixin.to_row(
            [('data_inicio__year', 3),
             ('data_inicio__month', 3),
             ('data_inicio__day', 3),
             ('tipo', 3)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Sessao Plenária'),
                     row1,
                     form_actions(save_label='Pesquisar'))
        )
