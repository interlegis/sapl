from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.utils.safestring import mark_safe

import crispy_layout_mixin
from crispy_layout_mixin import form_actions
from materia.models import MateriaLegislativa, TipoMateriaLegislativa

from .models import NormaJuridica

from sapl.utils import RANGE_ANOS

def get_esferas():
    return [('E', 'Estadual'),
            ('F', 'Federal'),
            ('M', 'Municipal')]


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))


class NormaJuridicaPesquisaForm(ModelForm):

    periodo_inicial = forms.DateField(label=u'Período Inicial',
                                      input_formats=['%d/%m/%Y'],
                                      required=False,
                                      widget=forms.DateInput(
                                        format='%d/%m/%Y',
                                        attrs={'class': 'dateinput'}))

    periodo_final = forms.DateField(label=u'Período Final',
                                    input_formats=['%d/%m/%Y'],
                                    required=False,
                                    widget=forms.DateInput(
                                        format='%d/%m/%Y',
                                        attrs={'class': 'dateinput'}))

    publicação_inicial = forms.DateField(label=u'Publicação Inicial',
                                         input_formats=['%d/%m/%Y'],
                                         required=False,
                                         widget=forms.DateInput(
                                            format='%d/%m/%Y',
                                            attrs={'class': 'dateinput'}))

    publicação_final = forms.DateField(label=u'Publicação Final',
                                       input_formats=['%d/%m/%Y'],
                                       required=False,
                                       widget=forms.DateInput(
                                            format='%d/%m/%Y',
                                            attrs={'class': 'dateinput'}))

    class Meta:
        model = NormaJuridica
        fields = ['tipo',
                  'numero',
                  'ano',
                  'periodo_inicial',
                  'periodo_final',
                  'publicação_inicial',
                  'publicação_final']

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 12)])

        row2 = crispy_layout_mixin.to_row(
            [('numero', 6), ('ano', 6)])

        row3 = crispy_layout_mixin.to_row(
            [('periodo_inicial', 6), ('periodo_final', 6)])

        row4 = crispy_layout_mixin.to_row(
            [('publicação_inicial', 6), ('publicação_final', 6)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
             Fieldset('Pesquisa Norma Juridica',
                      row1, row2, row3, row4),
             form_actions(save_label='Pesquisar')
        )
        super(NormaJuridicaPesquisaForm, self).__init__(*args, **kwargs)


class NormaJuridicaForm(ModelForm):

    # Campos de MateriaLegislativa
    tipo_materia = forms.ModelChoiceField(
        label='Matéria Legislativa',
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione'
    )
    numero_materia = forms.CharField(label='Número',
                                     required=False)
    ano_materia = forms.ChoiceField(label='Ano',
                                  required=False,
                                  choices=RANGE_ANOS)

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
                  ]

    def clean(self):
        data = super(NormaJuridicaForm, self).clean()

        if self.cleaned_data['tipo_materia']:
            try:
                materia = MateriaLegislativa.objects.get(
                        tipo=self.cleaned_data['tipo_materia'],
                        numero=self.cleaned_data['numero_materia'],
                        ano=self.cleaned_data['ano_materia'])
            except ObjectDoesNotExist:
                msg = 'Matéria adicionada não existe!'
                raise forms.ValidationError(msg)

        return data

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4), ('numero', 4), ('ano', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('data', 4), ('esfera_federacao', 4), ('complemento', 4)])

        row3 = crispy_layout_mixin.to_row(
            [('tipo_materia', 4), ('numero_materia', 4), ('ano_materia', 4)])

        row4 = crispy_layout_mixin.to_row(
            [('data_publicacao', 3), ('veiculo_publicacao', 3),
             ('pagina_inicio_publicacao', 3), ('pagina_fim_publicacao', 3)])

        row5 = crispy_layout_mixin.to_row(
            [('texto_integral', 12)])

        row6 = crispy_layout_mixin.to_row(
            [('ementa', 12)])

        row7 = crispy_layout_mixin.to_row(
            [('indexacao', 12)])

        row8 = crispy_layout_mixin.to_row(
            [('observacao', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Identificação Básica',
                     row1, row2, row3, row4, row5, row6, row7, row8),
            form_actions()
        )
        super(NormaJuridicaForm, self).__init__(*args, **kwargs)
