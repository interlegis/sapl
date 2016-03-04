"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from datetime import date

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Field, Fieldset, Layout, Submit
from django import forms
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
from crispy_layout_mixin import form_actions
from materia.models import TipoMateriaLegislativa

from .models import (Autor, DocumentoAcessorioAdministrativo,
                     DocumentoAdministrativo, TipoDocumentoAdministrativo,
                     TramitacaoAdministrativo)


def get_range_anos():
    return [('', 'Selecione')] \
        + [(year, year) for year in range(date.today().year, 1960, -1)]


def tramitacao():
    return [('', '--------'),
            (True, 'Sim'),
            (False, 'Não')]


TIPOS_PROTOCOLO = [('', 'Selecione'),
                   ('0', 'Enviado'),
                   ('1', 'Recebido')]


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))


class ProtocoloForm(forms.Form):

    YEARS = get_range_anos()

    tipo_protocolo = forms.ChoiceField(required=False,
                                       label=_('Tipo de Protocolo'),
                                       choices=TIPOS_PROTOCOLO,
                                       widget=forms.Select(
                                           attrs={'class': 'selector'}))

    numero_protocolo = forms.CharField(
        label=_('Número de Protocolo'), required=False)
    ano = forms.ChoiceField(required=False,
                            label='Ano',
                            choices=YEARS,
                            widget=forms.Select(
                                attrs={'class': 'selector'}))

    inicial = forms.DateField(label=_('Data Inicial'),
                              required=False,
                              widget=forms.TextInput(
                                  attrs={'class': 'dateinput'}))

    final = forms.DateField(label=_('Data Final'), required=False,
                            widget=forms.TextInput(
                                attrs={'class': 'dateinput'}))

    natureza_processo = forms.ChoiceField(required=False,
                                          label=_('Natureza Processo'),
                                          choices=[
                                              ('0', 'Administrativo'),
                                              ('1', 'Legislativo'),
                                              ('', 'Ambos')],
                                          # widget=forms.RadioSelect(
                                          #     renderer=HorizontalRadioRenderer)

                                          )

    tipo_documento = forms.ModelChoiceField(
        label=_('Tipo de Documento'),
        required=False,
        queryset=TipoDocumentoAdministrativo.objects.all(),
        empty_label='Selecione',
    )

    interessado = forms.CharField(label='Interessado', required=False)

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo de Matéria'),
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    autor = forms.ModelChoiceField(
        label='Autor',
        required=False,
        queryset=Autor.objects.all().order_by('tipo'),
        empty_label='Selecione',
    )

    assunto = forms.CharField(label='Assunto', required=False)

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('numero_protocolo', 6),
             ('ano', 6)])

        row2 = crispy_layout_mixin.to_row(
            [('inicial', 6),
             ('final', 6)])

        row3 = crispy_layout_mixin.to_row(
            [('tipo_documento', 4),
             ('tipo_protocolo', 4),
             ('tipo_materia', 4)])

        row4 = crispy_layout_mixin.to_row(
            [('interessado', 4),
             ('autor', 4),
             ('assunto', 4)])

        row5 = crispy_layout_mixin.to_row(
            [('natureza_processo', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(row1, row2,
                                    row3, row4,
                                    row5, form_actions(save_label='Pesquisar'))
        super(ProtocoloForm, self).__init__(
            *args, **kwargs)


class AnularProcoloAdmForm(forms.Form):

    YEARS = get_range_anos()

    numero_protocolo = forms.CharField(
        label=_('Número de Protocolo'), required=True)
    ano_protocolo = forms.ChoiceField(required=False,
                                      label='Ano',
                                      choices=YEARS,
                                      widget=forms.Select(
                                          attrs={'class': 'selector'}))
    justificativa_anulacao = forms.CharField(
        widget=forms.Textarea, label='Motivo', required=True)

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('numero_protocolo', 6),
             ('ano_protocolo', 6)])
        row2 = crispy_layout_mixin.to_row(
            [('justificativa_anulacao', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Identificação do Protocolo'),
                     row1,
                     row2,
                     HTML("&nbsp;"),
                     form_actions(save_label='Anular')
                     )
        )
        super(AnularProcoloAdmForm, self).__init__(
            *args, **kwargs)


class ProtocoloDocumentForm(forms.Form):

    NUMERACAO_CHOICES = [('1', _('Sequencial por Ano')),
                         ('2', _('Sequencial Único'))]

    numeracao = forms.ChoiceField(required=True,
                                  choices=NUMERACAO_CHOICES,
                                  widget=forms.RadioSelect(
                                      renderer=HorizontalRadioRenderer),
                                  label='')

    tipo_protocolo = forms.ChoiceField(required=True,
                                       label=_('Tipo de Protocolo'),
                                       choices=TIPOS_PROTOCOLO[1:],
                                       widget=forms.RadioSelect(
                                           renderer=HorizontalRadioRenderer))

    tipo_documento = forms.ModelChoiceField(
        label=_('Tipo de Documento'),
        required=False,
        queryset=TipoDocumentoAdministrativo.objects.all(),
        empty_label='Selecione',
    )

    num_paginas = forms.CharField(label=_('Núm. Páginas'), required=True)
    assunto = forms.CharField(
        widget=forms.Textarea, label='Assunto', required=True)

    interessado = forms.CharField(required=True,
                                  label='Interessado')

    observacao = forms.CharField(required=True,
                                 widget=forms.Textarea, label='Observação')

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('numeracao', 12)])
        row2 = crispy_layout_mixin.to_row(
            [('tipo_protocolo', 12)])
        row3 = crispy_layout_mixin.to_row(
            [('tipo_documento', 6),
             ('num_paginas', 6)])
        row4 = crispy_layout_mixin.to_row(
            [('assunto', 12)])
        row5 = crispy_layout_mixin.to_row(
            [('interessado', 12)])
        row6 = crispy_layout_mixin.to_row(
            [('observacao', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Protocolo - Opção de Numeração'), row1),
            Fieldset(_('Identificação de Documento'),
                     row2,
                     row3,
                     row4,
                     row5,
                     row6,
                     HTML("&nbsp;"),
                     form_actions(save_label=_('Protocolar Documento'))
                     )
        )
        super(ProtocoloDocumentForm, self).__init__(
            *args, **kwargs)


class ProtocoloMateriaForm(forms.Form):

    NUMERACAO_CHOICES = [('1', _('Sequencial por Ano')),
                         ('2', _('Sequencial Único'))]

    numeracao = forms.ChoiceField(required=True,
                                  choices=NUMERACAO_CHOICES,
                                  widget=forms.RadioSelect(
                                      renderer=HorizontalRadioRenderer),
                                  label='')

    tipo_protocolo = forms.ChoiceField(required=True,
                                       label=_('Tipo de Protocolo'),
                                       choices=TIPOS_PROTOCOLO[1:],
                                       widget=forms.RadioSelect(
                                           renderer=HorizontalRadioRenderer))

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo de Matéria'),
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    num_paginas = forms.CharField(label=_('Núm. Páginas'), required=True)
    ementa = forms.CharField(
        widget=forms.Textarea, label='Ementa', required=True)

    autor = forms.ModelChoiceField(
        label='Autor',
        required=False,
        queryset=Autor.objects.all().order_by('tipo'),
        empty_label='Selecione',
    )

    observacao = forms.CharField(required=True,
                                 widget=forms.Textarea,
                                 label='Observação')

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('numeracao', 12)])
        row2 = crispy_layout_mixin.to_row(
            [('tipo_materia', 6),
             ('num_paginas', 6)])
        row3 = crispy_layout_mixin.to_row(
            [('ementa', 12)])
        row4 = crispy_layout_mixin.to_row(
            [('autor', 12)])
        row5 = crispy_layout_mixin.to_row(
            [('observacao', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Protocolo - Opção de Numeração'), row1),
            Fieldset(_('Identificação da Matéria'),
                     row2,
                     row3,
                     row4,
                     row5,
                     HTML("&nbsp;"),
                     form_actions(save_label=_('Protocolar Matéria'))
                     )
        )
        super(ProtocoloMateriaForm, self).__init__(
            *args, **kwargs)


class ProposicaoSimpleForm(forms.Form):

    tipo = forms.CharField(label='Tipo',
                           widget=forms.TextInput(
                               attrs={'readonly': 'readonly'}))
    materia = forms.CharField(label='Matéria',
                              widget=forms.TextInput(
                                  attrs={'readonly': 'readonly'}))
    data_envio = forms.DateField(label=_('Data Envio'),
                                 widget=forms.DateInput(
                                     format='%d/%m/%Y',
                                     attrs={'readonly': 'readonly'}))
    data_recebimento = forms.DateField(label=_('Data Recebimento'),
                                       widget=forms.DateInput(
                                           format='%d/%m/%Y',
                                           attrs={'readonly': 'readonly'}))

    descricao = forms.CharField(label='Descrição',
                                widget=forms.TextInput(
                                    attrs={'readonly': 'readonly'}))

    numero_proposicao = forms.CharField(label='Número',
                                        widget=forms.TextInput(
                                            attrs={'readonly': 'readonly'}))
    # ano = forms.CharField(label='Ano',
    #                             widget = forms.TextInput(
    #                               attrs={'readonly':'readonly'}))


class DocumentoAcessorioAdministrativoForm(ModelForm):

    data = forms.DateField(label=u'Data', input_formats=['%d/%m/%Y'],
                           required=False,
                           widget=forms.DateInput(format='%d/%m/%Y'))

    class Meta:
        model = DocumentoAcessorioAdministrativo
        fields = ['tipo',
                  'nome',
                  'data',
                  'autor',
                  'arquivo',
                  'assunto']

    def __init__(self, excluir=False, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4),
             ('nome', 4),
             ('data', 4)])
        row2 = crispy_layout_mixin.to_row(
            [('autor', 12)])
        row3 = crispy_layout_mixin.to_row(
            [('arquivo', 12)])
        row4 = crispy_layout_mixin.to_row(
            [('assunto', 12)])

        more = []
        if excluir:
            more = [Submit('Excluir', 'Excluir')]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Incluir Documento Acessório'),
                row1, row2, row3, row4,
                form_actions(more=more)
            )
        )
        super(DocumentoAcessorioAdministrativoForm, self).__init__(
            *args, **kwargs)


class TramitacaoAdmForm(ModelForm):

    data_tramitacao = forms.DateField(label=u'Data Tramitação',
                                      input_formats=['%d/%m/%Y'],
                                      required=False,
                                      widget=forms.DateInput(
                                          format='%d/%m/%Y',
                                          attrs={'class': 'dateinput'}))

    data_encaminhamento = forms.DateField(label=u'Data Encaminhamento',
                                          input_formats=['%d/%m/%Y'],
                                          required=False,
                                          widget=forms.DateInput(
                                              format='%d/%m/%Y',
                                              attrs={'class': 'dateinput'}))

    data_fim_prazo = forms.DateField(label=u'Data Fim Prazo',
                                     input_formats=['%d/%m/%Y'],
                                     required=False,
                                     widget=forms.DateInput(
                                         format='%d/%m/%Y',
                                         attrs={'class': 'dateinput'}))

    class Meta:
        model = TramitacaoAdministrativo
        fields = ['data_tramitacao',
                  'unidade_tramitacao_local',
                  'status',
                  'unidade_tramitacao_destino',
                  'data_encaminhamento',
                  'data_fim_prazo',
                  'texto',
                  'documento',
                  ]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Incluir Tramitação'),
                     'data_tramitacao',
                     'unidade_tramitacao_local',
                     'status',
                     'unidade_tramitacao_destino',
                     'data_encaminhamento',
                     'data_fim_prazo',
                     'texto'),
            Field('documento', type="hidden"),
            form_actions()
        )
        super(TramitacaoAdmForm, self).__init__(
            *args, **kwargs)


class DocumentoAdministrativoForm(ModelForm):

    class Meta:
        model = DocumentoAdministrativo
        fields = ['tipo',
                  'numero',
                  'ano',
                  'data',
                  'numero_protocolo',
                  'assunto',
                  'interessado',
                  'tramitacao',
                  'dias_prazo',
                  'data_fim_prazo',
                  'observacao',
                  'texto_integral',
                  ]

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4), ('numero', 4), ('ano', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('data', 6), ('numero_protocolo', 6)])

        row3 = crispy_layout_mixin.to_row(
            [('assunto', 12)])

        row4 = crispy_layout_mixin.to_row(
            [('interessado', 9), ('tramitacao', 3)])

        row5 = crispy_layout_mixin.to_row(
            [('texto_integral', 12)])

        row6 = crispy_layout_mixin.to_row(
            [('dias_prazo', 6), ('data_fim_prazo', 6)])

        row7 = crispy_layout_mixin.to_row(
            [('observacao', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Identificação Básica'),
                     row1, row2, row3, row4, row5),
            Fieldset(_('Outras Informações'),
                     row6, row7),
            form_actions(more=[Submit('Excluir', 'Excluir')]),
        )
        super(DocumentoAdministrativoForm, self).__init__(
            *args, **kwargs)
