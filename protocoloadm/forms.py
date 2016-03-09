from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Field, Fieldset, Layout, Submit
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
from crispy_layout_mixin import form_actions
from materia.models import TipoMateriaLegislativa
from sapl.utils import RANGE_ANOS

from .models import (Autor, DocumentoAcessorioAdministrativo,
                     DocumentoAdministrativo, Protocolo,
                     TipoDocumentoAdministrativo, TramitacaoAdministrativo)

TRAMITACAO = [(True, 'Sim'), (False, 'Não')]

TIPOS_PROTOCOLO = [('0', 'Enviado'), ('1', 'Recebido')]

NATUREZA_PROCESSO = [('0', 'Administrativo'),
                     ('1', 'Legislativo'),
                     ('', 'Ambos')]


class HorizontalRadioRenderer(forms.RadioSelect.renderer):

    def render(self):
        return mark_safe(u' '.join([u'%s ' % w for w in self]))


class ProtocoloForm(forms.Form):

    tipo_protocolo = forms.ChoiceField(required=False,
                                       label=_('Tipo de Protocolo'),
                                       choices=TIPOS_PROTOCOLO,
                                       widget=forms.Select(
                                           attrs={'class': 'selector'}))

    numero_protocolo = forms.CharField(
        label=_('Número de Protocolo'), required=False)
    ano = forms.ChoiceField(required=False,
                            label='Ano',
                            choices=RANGE_ANOS,
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
                                          choices=NATUREZA_PROCESSO,
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


class AnularProcoloAdmForm(ModelForm):

    numero = forms.CharField(required=True,
                             label=Protocolo._meta.
                             get_field('numero').verbose_name
                             )
    ano = forms.ChoiceField(required=True,
                            label=Protocolo._meta.
                            get_field('ano').verbose_name,
                            choices=RANGE_ANOS,
                            widget=forms.Select(attrs={'class': 'selector'}))
    justificativa_anulacao = forms.CharField(required=True,
                                             label=Protocolo._meta.
                                             get_field('justificativa_anulacao'
                                                      ).verbose_name,
                                             widget=forms.Textarea)

    def clean(self):
        cleaned_data = super(AnularProcoloAdmForm, self).clean()

        numero = cleaned_data.get("numero")
        ano = cleaned_data.get("ano")

        # se não inserido numero ou ano não prosseguir
        # (e ele vai falhar pq numero e ano são obrigatórios)
        if not numero or not ano:
            return

        try:
            protocolo = Protocolo.objects.get(numero=numero, ano=ano)

            if protocolo.anulado:
                raise forms.ValidationError(
                    _("Protocolo %s/%s já encontra-se anulado")
                    % (numero, ano))
        except ObjectDoesNotExist:
            raise forms.ValidationError(
                    _("Protocolo %s/%s não existe" % (numero, ano)))

    class Meta:
        model = Protocolo
        fields = ['numero',
                  'ano',
                  'justificativa_anulacao',
                  'anulado',
                  'user_anulacao',
                  'ip_anulacao',
                  ]
        widgets = {'anulado': forms.HiddenInput(),
                   'user_anulacao': forms.HiddenInput(),
                   'ip_anulacao': forms.HiddenInput(),
                   }

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('numero', 6),
             ('ano', 6)])
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


class ProtocoloDocumentForm(ModelForm):

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

    class Meta:
        model = Protocolo
        fields = ['numeracao',
                  'tipo_protocolo',
                  'tipo_documento',
                  'num_paginas',
                  'assunto',
                  'interessado',
                  'observacao',
                  ]

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


class ProtocoloMateriaForm(ModelForm):

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

    class Meta:
        model = Protocolo
        fields = ['numeracao',
                  'tipo_protocolo',
                  'tipo_materia',
                  'num_paginas',
                  'ementa',
                  'autor',
                  'observacao',
                  ]

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('numeracao', 12)])
        row2 = crispy_layout_mixin.to_row(
            [('tipo_materia', 4),
             ('tipo_protocolo', 4),
             ('num_paginas', 4)])
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

    class Meta:
        model = DocumentoAcessorioAdministrativo
        fields = ['tipo',
                  'nome',
                  'data',
                  'autor',
                  'arquivo',
                  'assunto']

        widgets = {
            'data': forms.DateInput(format='%d/%m/%Y')
        }

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

        widgets = {
            'data_tramitacao': forms.DateInput(format='%d/%m/%Y'),
            'data_encaminhamento': forms.DateInput(format='%d/%m/%Y'),
            'data_fim_prazo': forms.DateInput(format='%d/%m/%Y'),
        }

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
