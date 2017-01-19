from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.forms import ModelForm, widgets
from django.utils.translation import ugettext_lazy as _
import django_filters

from sapl.crispy_layout_mixin import form_actions, to_row
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.settings import MAX_DOC_UPLOAD_SIZE
from sapl.utils import RANGE_ANOS, RANGE_ANOS_COM_EMPTY_LABEL, RangeWidgetOverride

from .models import (AssuntoNorma, NormaJuridica, NormaRelacionada,
                     TipoNormaJuridica)


def get_esferas():
    return [('E', 'Estadual'),
            ('F', 'Federal'),
            ('M', 'Municipal')]


YES_NO_CHOICES = [('', '---------'),
                  (True, _('Sim')),
                  (False, _('Não'))]

ORDENACAO_CHOICES = [('', '---------'),
                     ('tipo,ano,numero', _('Tipo/Ano/Número')),
                     ('data,tipo,ano,numero', _('Data/Tipo/Ano/Número'))]


class NormaFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    ano = django_filters.ChoiceFilter(required=False,
                                      label=u'Ano',
                                      choices=RANGE_ANOS_COM_EMPTY_LABEL)

    ementa = django_filters.CharFilter(lookup_expr='icontains')

    assuntos = django_filters.ModelChoiceFilter(
        queryset=AssuntoNorma.objects.all())

    class Meta:
        model = NormaJuridica
        fields = ['tipo', 'numero', 'ano', 'data',
                  'data_publicacao', 'ementa', 'assuntos']

    def __init__(self, *args, **kwargs):
        super(NormaFilterSet, self).__init__(*args, **kwargs)

        row1 = to_row([('tipo', 4), ('numero', 4), ('ano', 4)])
        row2 = to_row([('data', 6), ('data_publicacao', 6)])
        row3 = to_row([('ementa', 8), ('assuntos', 4)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Norma'),
                     row1, row2, row3,
                     form_actions(save_label='Pesquisar'))
        )


class NormaJuridicaForm(ModelForm):

    # Campos de MateriaLegislativa
    tipo_materia = forms.ModelChoiceField(
        label='Matéria',
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione'
    )
    numero_materia = forms.CharField(
        label='Número Matéria',
        required=False
    )
    ano_materia = forms.ChoiceField(
        label='Ano Matéria',
        required=False,
        choices=RANGE_ANOS_COM_EMPTY_LABEL,
    )

    class Meta:
        model = NormaJuridica
        fields = ['tipo',
                  'numero',
                  'ano',
                  'data',
                  'esfera_federacao',
                  'complemento',
                  'tipo_materia',
                  'numero_materia',
                  'ano_materia',
                  'data_publicacao',
                  'veiculo_publicacao',
                  'pagina_inicio_publicacao',
                  'pagina_fim_publicacao',
                  'ementa',
                  'indexacao',
                  'observacao',
                  'texto_integral',
                  'assuntos']
        widgets = {'assuntos': widgets.CheckboxSelectMultiple}

    def clean(self):
        cleaned_data = self.cleaned_data

        if (cleaned_data['tipo_materia'] and
            cleaned_data['numero_materia'] and
                cleaned_data['ano_materia']):

            try:
                materia = MateriaLegislativa.objects.get(
                    tipo_id=cleaned_data['tipo_materia'],
                    numero=cleaned_data['numero_materia'],
                    ano=cleaned_data['ano_materia'])
            except ObjectDoesNotExist:
                raise forms.ValidationError("Matéria escolhida não existe!")
            else:
                cleaned_data['materia'] = materia

        else:
            cleaned_data['materia'] = None
        return cleaned_data

    def clean_texto_integral(self):
        texto_integral = self.cleaned_data.get('texto_integral', False)
        if texto_integral:
            if texto_integral.size > MAX_DOC_UPLOAD_SIZE:
                raise ValidationError("Arquivo muito grande. ( > 5mb )")
            return texto_integral

    def save(self, commit=False):
        norma = self.instance
        norma.timestamp = datetime.now()
        norma.materia = self.cleaned_data['materia']
        norma = super(NormaJuridicaForm, self).save(commit=True)
        return norma


class NormaRelacionadaForm(ModelForm):

    tipo = forms.ModelChoiceField(
        label='Tipo',
        required=True,
        queryset=TipoNormaJuridica.objects.all(),
        empty_label='----------',
    )
    numero = forms.CharField(label='Número', required=True)
    ano = forms.CharField(label='Ano', required=True)
    ementa = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'disabled': 'disabled'}))

    class Meta:
        model = NormaRelacionada
        fields = ['tipo', 'numero', 'ano', 'ementa', 'tipo_vinculo']

    def __init__(self, *args, **kwargs):
        super(NormaRelacionadaForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.errors:
            return self.errors
        cleaned_data = self.cleaned_data

        try:
            norma_relacionada = NormaJuridica.objects.get(
                numero=cleaned_data['numero'],
                ano=cleaned_data['ano'],
                tipo=cleaned_data['tipo'])
        except ObjectDoesNotExist:
            msg = _('A norma a ser relacionada não existe.')
            raise ValidationError(msg)
        else:
            cleaned_data['norma_relacionada'] = norma_relacionada

        return cleaned_data

    def save(self, commit=False):
        relacionada = super(NormaRelacionadaForm, self).save(commit)
        relacionada.norma_relacionada = self.cleaned_data['norma_relacionada']
        relacionada.save()
        return relacionada
