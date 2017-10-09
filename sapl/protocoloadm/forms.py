
import django_filters
from crispy_forms.bootstrap import InlineRadios
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Fieldset, Layout
from django import forms
from django.core.exceptions import (MultipleObjectsReturned,
                                    ObjectDoesNotExist, ValidationError)
from django.db import models
from django.forms import ModelForm
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import Autor, TipoAutor
from sapl.crispy_layout_mixin import SaplFormLayout, form_actions, to_row
from sapl.materia.models import (MateriaLegislativa, TipoMateriaLegislativa,
                                 UnidadeTramitacao)
from sapl.utils import (RANGE_ANOS, AnoNumeroOrderingFilter,
                        RangeWidgetOverride, autor_label, autor_modal)

from .models import (DocumentoAcessorioAdministrativo, DocumentoAdministrativo,
                     Protocolo, TipoDocumentoAdministrativo,
                     TramitacaoAdministrativo)

TIPOS_PROTOCOLO = [('0', 'Recebido'), ('1', 'Enviado'), ('', 'Ambos')]
TIPOS_PROTOCOLO_CREATE = [('0', 'Recebido'), ('1', 'Enviado')]

NATUREZA_PROCESSO = [('', 'Ambos'),
                     ('0', 'Administrativo'),
                     ('1', 'Legislativo')]


def ANO_CHOICES():
    return [('', '---------')] + RANGE_ANOS


EM_TRAMITACAO = [('', 'Tanto Faz'),
                 (0, 'Sim'),
                 (1, 'Não')]


class ProtocoloFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': 'Data (%s)' % (_('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    ano = django_filters.ChoiceFilter(required=False,
                                      label='Ano',
                                      choices=ANO_CHOICES)

    assunto_ementa = django_filters.CharFilter(lookup_expr='icontains')

    interessado = django_filters.CharFilter(lookup_expr='icontains')

    autor = django_filters.CharFilter(widget=forms.HiddenInput())

    tipo_protocolo = django_filters.ChoiceFilter(
        required=False,
        label='Tipo de Protocolo',
        choices=TIPOS_PROTOCOLO,
        widget=forms.Select(
            attrs={'class': 'selector'}))
    tipo_processo = django_filters.ChoiceFilter(
        required=False,
        label='Natureza do Processo',
        choices=NATUREZA_PROCESSO,
        widget=forms.Select(
            attrs={'class': 'selector'}))

    o = AnoNumeroOrderingFilter()

    class Meta:
        model = Protocolo
        fields = ['numero',
                  'tipo_documento',
                  'data',
                  'tipo_materia',
                  ]

    def __init__(self, *args, **kwargs):
        super(ProtocoloFilterSet, self).__init__(*args, **kwargs)

        self.filters['autor'].label = 'Tipo de Matéria'
        self.filters['assunto_ementa'].label = 'Assunto'

        row1 = to_row(
            [('numero', 4),
             ('ano', 4),
             ('data', 4)])

        row2 = to_row(
            [('tipo_documento', 4),
             ('tipo_protocolo', 4),
             ('tipo_materia', 4)])

        row3 = to_row(
            [('interessado', 6),
             ('assunto_ementa', 6)])

        row4 = to_row(
            [('autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'Limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])
        row5 = to_row(
            [('tipo_processo', 12)])
        row6 = to_row(
            [('o', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar Protocolo'),
                     row1, row2,
                     row3,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row4, row5, row6,
                     form_actions(save_label='Pesquisar'))
        )


class DocumentoAdministrativoFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': 'Data (%s)' % (_('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    ano = django_filters.ChoiceFilter(required=False,
                                      label='Ano',
                                      choices=ANO_CHOICES)

    tramitacao = django_filters.ChoiceFilter(required=False,
                                             label='Em Tramitação?',
                                             choices=EM_TRAMITACAO)

    assunto = django_filters.CharFilter(lookup_expr='icontains')

    interessado = django_filters.CharFilter(lookup_expr='icontains')

    o = AnoNumeroOrderingFilter()

    class Meta:
        model = DocumentoAdministrativo
        fields = ['tipo',
                  'numero',
                  'protocolo__numero',
                  'data',
                  'tramitacaoadministrativo__unidade_tramitacao_destino',
                  'tramitacaoadministrativo__status']

    def __init__(self, *args, **kwargs):
        super(DocumentoAdministrativoFilterSet, self).__init__(*args, **kwargs)

        local_atual = 'tramitacaoadministrativo__unidade_tramitacao_destino'
        self.filters['tipo'].label = 'Tipo de Documento'
        self.filters['tramitacaoadministrativo__status'].label = 'Situação'
        self.filters[local_atual].label = 'Localização Atual'

        row1 = to_row(
            [('tipo', 6),
             ('numero', 6)])

        row2 = to_row(
            [('ano', 4),
             ('protocolo__numero', 4),
             ('data', 4)])

        row3 = to_row(
            [('interessado', 4),
             ('assunto', 4),
             ('tramitacao', 4)])

        row4 = to_row(
            [('tramitacaoadministrativo__unidade_tramitacao_destino', 6),
             ('tramitacaoadministrativo__status', 6)])

        row5 = to_row(
            [('o', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar Documento'),
                     row1, row2,
                     row3, row4, row5,
                     form_actions(save_label='Pesquisar'))
        )


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
    justificativa_anulacao = forms.CharField(
        required=True,
        label=Protocolo._meta.get_field('justificativa_anulacao').verbose_name,
        widget=forms.Textarea)

    def clean(self):
        super(AnularProcoloAdmForm, self).clean()

        cleaned_data = super(AnularProcoloAdmForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        numero = cleaned_data['numero']
        ano = cleaned_data['ano']

        try:
            protocolo = Protocolo.objects.get(numero=numero, ano=ano)
            if protocolo.anulado:
                raise forms.ValidationError(
                    _("Protocolo %s/%s já encontra-se anulado")
                    % (numero, ano))
        except ObjectDoesNotExist:
            raise forms.ValidationError(
                _("Protocolo %s/%s não existe" % (numero, ano)))

        exists = False
        if protocolo.tipo_materia:
            exists = MateriaLegislativa.objects.filter(
                numero_protocolo=protocolo.numero, ano=protocolo.ano).exists()
        elif protocolo.tipo_documento:
            exists = protocolo.documentoadministrativo_set.all(
            ).order_by('-ano', '-numero').exists()

        if exists:
            raise forms.ValidationError(
                _("Protocolo %s/%s não pode ser removido pois existem "
                    "documentos vinculados a ele." % (numero, ano)))

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

        row1 = to_row(
            [('numero', 6),
             ('ano', 6)])
        row2 = to_row(
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

    tipo_protocolo = forms.ChoiceField(required=True,
                                       label=_('Tipo de Protocolo'),
                                       choices=TIPOS_PROTOCOLO_CREATE,)

    tipo_documento = forms.ModelChoiceField(
        label=_('Tipo de Documento'),
        required=True,
        queryset=TipoDocumentoAdministrativo.objects.all(),
        empty_label='Selecione',
    )

    numero_paginas = forms.CharField(label=_('Núm. Páginas'), required=True)
    assunto = forms.CharField(
        widget=forms.Textarea, label='Assunto', required=True)

    interessado = forms.CharField(required=True,
                                  label='Interessado')

    observacao = forms.CharField(required=False,
                                 widget=forms.Textarea, label='Observação')

    class Meta:
        model = Protocolo
        fields = ['tipo_protocolo',
                  'tipo_documento',
                  'numero_paginas',
                  'assunto',
                  'interessado',
                  'observacao',
                  ]

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [(InlineRadios('tipo_protocolo'), 12)])
        row2 = to_row(
            [('tipo_documento', 6),
             ('numero_paginas', 6)])
        row3 = to_row(
            [('assunto', 12)])
        row4 = to_row(
            [('interessado', 12)])
        row5 = to_row(
            [('observacao', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Identificação de Documento'),
                     row1,
                     row2,
                     row3,
                     row4,
                     row5,
                     HTML("&nbsp;"),
                     form_actions(save_label=_('Protocolar Documento'))
                     )
        )
        super(ProtocoloDocumentForm, self).__init__(
            *args, **kwargs)


class ProtocoloMateriaForm(ModelForm):
    autor = forms.ModelChoiceField(required=True,
                                   empty_label='------',
                                   queryset=Autor.objects.all()
                                   )

    tipo_autor = forms.ModelChoiceField(required=True,
                                        empty_label='------',
                                        queryset=TipoAutor.objects.all()
                                        )

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo de Matéria'),
        required=True,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero_paginas = forms.CharField(label=_('Núm. Páginas'), required=True)

    observacao = forms.CharField(required=False,
                                 widget=forms.Textarea, label='Observação')

    assunto_ementa = forms.CharField(required=True,
                                     widget=forms.Textarea, label='Ementa')

    class Meta:
        model = Protocolo
        fields = ['tipo_materia',
                  'numero_paginas',
                  'autor',
                  'tipo_autor',
                  'assunto_ementa',
                  'observacao']

    def clean_autor(self):
        autor_field = self.cleaned_data['autor']
        try:
            autor = Autor.objects.get(id=autor_field.id)
        except ObjectDoesNotExist:
            autor_field = None
        else:
            autor_field = autor
        return autor_field

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [('tipo_materia', 4),
             ('numero_paginas', 2),
             ('tipo_autor', 3),
             ('autor', 3)])
        row3 = to_row(
            [('assunto_ementa', 12)])
        row4 = to_row(
            [('observacao', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Identificação da Matéria'),
                     row1, row3,
                     row4, form_actions(save_label='Protocolar Matéria')))

        super(ProtocoloMateriaForm, self).__init__(
            *args, **kwargs)


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
                  ]

    def clean(self):
        cleaned_data = super(TramitacaoAdmForm, self).clean()

        if 'data_encaminhamento' in cleaned_data:
            data_enc_form = cleaned_data['data_encaminhamento']
        if 'data_fim_prazo' in cleaned_data:
            data_prazo_form = cleaned_data['data_fim_prazo']
        if 'data_tramitacao' in cleaned_data:
            data_tram_form = cleaned_data['data_tramitacao']

        if not self.is_valid():
            return cleaned_data

        ultima_tramitacao = TramitacaoAdministrativo.objects.filter(
            documento_id=self.instance.documento_id).exclude(
            id=self.instance.id).order_by(
            '-data_tramitacao',
            '-id').first()

        if not self.instance.data_tramitacao:
            if ultima_tramitacao:
                destino = ultima_tramitacao.unidade_tramitacao_destino
                if (destino != self.cleaned_data['unidade_tramitacao_local']):
                    msg = _('A origem da nova tramitação deve ser igual ao '
                            'destino  da última adicionada!')
                    raise ValidationError(msg)

            if self.cleaned_data['data_tramitacao'] > timezone.now().date():
                msg = _(
                    'A data de tramitação deve ser ' +
                    'menor ou igual a data de hoje!')
                raise ValidationError(msg)

            if (ultima_tramitacao and
                    data_tram_form < ultima_tramitacao.data_tramitacao):
                msg = _('A data da nova tramitação deve ser ' +
                        'maior que a data da última tramitação!')
                raise ValidationError(msg)

        if data_enc_form:
            if data_enc_form < data_tram_form:
                msg = _('A data de encaminhamento deve ser ' +
                        'maior que a data de tramitação!')
                raise ValidationError(msg)

        if data_prazo_form:
            if data_prazo_form < data_tram_form:
                msg = _('A data fim de prazo deve ser ' +
                        'maior que a data de tramitação!')
                raise ValidationError(msg)

        return self.cleaned_data


class TramitacaoAdmEditForm(TramitacaoAdmForm):

    unidade_tramitacao_local = forms.ModelChoiceField(
        queryset=UnidadeTramitacao.objects.all(),
        widget=forms.HiddenInput())

    data_tramitacao = forms.DateField(widget=forms.HiddenInput())

    class Meta:
        model = TramitacaoAdministrativo
        fields = ['data_tramitacao',
                  'unidade_tramitacao_local',
                  'status',
                  'unidade_tramitacao_destino',
                  'data_encaminhamento',
                  'data_fim_prazo',
                  'texto',
                  ]

    def clean(self):
        ultima_tramitacao = TramitacaoAdministrativo.objects.filter(
            documento_id=self.instance.documento_id).order_by(
            '-data_tramitacao',
            '-id').first()

        # Se a Tramitação que está sendo editada não for a mais recente,
        # ela não pode ter seu destino alterado.
        if ultima_tramitacao != self.instance:
            if self.cleaned_data['unidade_tramitacao_destino'] != \
                    self.instance.unidade_tramitacao_destino:
                raise ValidationError(
                    'Você não pode mudar a Unidade de Destino desta '
                    'tramitação, pois irá conflitar com a Unidade '
                    'Local da tramitação seguinte')

        self.cleaned_data['data_tramitacao'] = \
            self.instance.data_tramitacao
        self.cleaned_data['unidade_tramitacao_local'] = \
            self.instance.unidade_tramitacao_local

        return super(TramitacaoAdmEditForm, self).clean()


class DocumentoAdministrativoForm(ModelForm):

    data = forms.DateField(initial=timezone.now)

    ano_protocolo = forms.ChoiceField(required=False,
                                      label=Protocolo._meta.
                                      get_field('ano').verbose_name,
                                      choices=RANGE_ANOS,
                                      widget=forms.Select(
                                          attrs={'class': 'selector'}))

    numero_protocolo = forms.IntegerField(required=False,
                                          label=Protocolo._meta.
                                          get_field('numero').verbose_name)

    class Meta:
        model = DocumentoAdministrativo
        fields = ['tipo',
                  'numero',
                  'ano',
                  'data',
                  'numero_protocolo',
                  'ano_protocolo',
                  'assunto',
                  'interessado',
                  'tramitacao',
                  'dias_prazo',
                  'data_fim_prazo',
                  'observacao',
                  'texto_integral',
                  'protocolo',
                  ]

        widgets = {'protocolo': forms.HiddenInput()}

    def clean(self):
        super(DocumentoAdministrativoForm, self).clean()

        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        numero_protocolo = self.data['numero_protocolo']
        ano_protocolo = self.data['ano_protocolo']

        # campos opcionais, mas que se informados devem ser válidos
        if numero_protocolo and ano_protocolo:
            try:
                self.fields['protocolo'].initial = Protocolo.objects.get(
                    numero=numero_protocolo,
                    ano=ano_protocolo).pk
            except ObjectDoesNotExist:
                msg = _('Protocolo %s/%s inexistente.' % (
                    numero_protocolo, ano_protocolo))
                raise ValidationError(msg)
            except MultipleObjectsReturned:
                msg = _(
                    'Existe mais de um Protocolo com este ano e número.' % (
                    numero_protocolo, ano_protocolo))
                raise ValidationError(msg)

        return self.cleaned_data

    def save(self, commit=True):
        documento = super(DocumentoAdministrativoForm, self).save(False)
        if self.fields['protocolo'].initial:
            documento.protocolo = Protocolo.objects.get(
                id=int(self.fields['protocolo'].initial))

        documento.save()

        return documento

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [('tipo', 4), ('numero', 4), ('ano', 4)])

        row2 = to_row(
            [('data', 4), ('numero_protocolo', 4), ('ano_protocolo', 4)])

        row3 = to_row(
            [('assunto', 12)])

        row4 = to_row(
            [('interessado', 9), ('tramitacao', 3)])

        row5 = to_row(
            [('texto_integral', 12)])

        row6 = to_row(
            [('dias_prazo', 6), ('data_fim_prazo', 6)])

        row7 = to_row(
            [('observacao', 12)])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2, row3, row4, row5),
            Fieldset(_('Outras Informações'),
                     row6, row7))
        super(DocumentoAdministrativoForm, self).__init__(
            *args, **kwargs)
