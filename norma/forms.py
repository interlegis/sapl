"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
from crispy_layout_mixin import form_actions
from materia.models import TipoMateriaLegislativa

from .models import NormaJuridica


def get_esferas():
    return [('E', 'Estadual'),
            ('F', 'Federal'),
            ('M', 'Municipal')]


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))


class NormaJuridicaForm(ModelForm):

    tipo_materia = forms.ModelChoiceField(
        label=_('Matéria Legislativa'),
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione'
        )

    numero_materia = forms.CharField(label='Número', required=False)

    ano_materia = forms.CharField(label='Ano', required=False)

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
                  'texto_integral']

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4),
             ('numero', 4),
             ('ano', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('data', 4),
             ('esfera_federacao', 4),
             ('complemento', 4)])

        row3 = crispy_layout_mixin.to_row(
            [('tipo_materia', 4),
             ('numero_materia', 4),
             ('ano_materia', 4)])

        row4 = crispy_layout_mixin.to_row(
            [('data_publicacao', 3),
             ('veiculo_publicacao', 3),
             ('pagina_inicio_publicacao', 3),
             ('pagina_fim_publicacao', 3)])

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
            Fieldset(_('Cadastro de Norma Jurídica'),
                     Fieldset(_('Identificação Básica'),
                              row1, row2, row3, row4, row5, row6, row7, row8),
                     form_actions()
                     )
        )
        super(NormaJuridicaForm, self).__init__(*args, **kwargs)
