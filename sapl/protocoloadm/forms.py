
import logging

from crispy_forms.bootstrap import InlineRadios, Alert
from sapl.crispy_layout_mixin import SaplFormHelper
from crispy_forms.layout import HTML, Button, Column, Fieldset, Layout, Div
from django import forms
from django.core.exceptions import (MultipleObjectsReturned,
                                    ObjectDoesNotExist, ValidationError)
from django.db import models
from django.db.models import Max
from django.forms import ModelForm
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import django_filters

from sapl.base.models import Autor, TipoAutor, AppConfig
from sapl.crispy_layout_mixin import SaplFormLayout, form_actions, to_row
from sapl.materia.models import (MateriaLegislativa, TipoMateriaLegislativa,
                                 UnidadeTramitacao)
from sapl.protocoloadm.models import Protocolo
from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES, AnoNumeroOrderingFilter,
                        RangeWidgetOverride, autor_label, autor_modal,
                        choice_anos_com_protocolo, choice_force_optional,
                        choice_anos_com_documentoadministrativo,
                        FilterOverridesMetaMixin, choice_anos_com_materias,
                        FileFieldCheckMixin)

from .models import (AcompanhamentoDocumento, DocumentoAcessorioAdministrativo,
                     DocumentoAdministrativo,
                     Protocolo, TipoDocumentoAdministrativo,
                     TramitacaoAdministrativo, Anexado)


TIPOS_PROTOCOLO = [('0', 'Recebido'), ('1', 'Enviado'),
                   ('2', 'Interno')]
TIPOS_PROTOCOLO_CREATE = [
    ('0', 'Recebido'), ('1', 'Enviado'), ('2', 'Interno')]

NATUREZA_PROCESSO = [('0', 'Administrativo'),
                     ('1', 'Legislativo')]


EM_TRAMITACAO = [(0, 'Sim'), (1, 'Não')]


class AcompanhamentoDocumentoForm(ModelForm):

    class Meta:
        model = AcompanhamentoDocumento
        fields = ['email']

    def __init__(self, *args, **kwargs):

        row1 = to_row([('email', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Acompanhamento de Documento por e-mail'),
                row1,
                form_actions(label='Cadastrar')
            )
        )
        super(AcompanhamentoDocumentoForm, self).__init__(*args, **kwargs)


class ProtocoloFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(
        required=False,
        label='Ano',
        choices=choice_anos_com_protocolo)

    assunto_ementa = django_filters.CharFilter(
        label=_('Assunto'),
        lookup_expr='icontains')

    interessado = django_filters.CharFilter(
        label=_('Interessado'),
        lookup_expr='icontains')

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

    o = AnoNumeroOrderingFilter(help_text='')

    class Meta(FilterOverridesMetaMixin):
        model = Protocolo
        fields = ['numero',
                  'tipo_documento',
                  'timestamp',
                  'tipo_materia',
                  ]

    def __init__(self, *args, **kwargs):
        super(ProtocoloFilterSet, self).__init__(*args, **kwargs)

        self.filters['timestamp'].label = 'Data (Inicial - Final)'

        row1 = to_row(
            [('numero', 4),
             ('ano', 4),
             ('timestamp', 4)])

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
            [('tipo_processo', 6), ('o', 6)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar Protocolo'),
                     row1, row2,
                     row3,
                     row5,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row4,
                     form_actions(label='Pesquisar'))
        )


class DocumentoAdministrativoFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(
        required=False,
        label='Ano',
        choices=choice_anos_com_documentoadministrativo)

    tramitacao = django_filters.ChoiceFilter(required=False,
                                             label='Em Tramitação?',
                                             choices=YES_NO_CHOICES)

    assunto = django_filters.CharFilter(
        label=_('Assunto'),
        lookup_expr='icontains')

    interessado = django_filters.CharFilter(
        label=_('Interessado'),
        lookup_expr='icontains')

    o = AnoNumeroOrderingFilter(help_text='')

    class Meta(FilterOverridesMetaMixin):
        model = DocumentoAdministrativo
        fields = ['tipo',
                  'numero',
                  'protocolo__numero',
                  'numero_externo',
                  'data',
                  'tramitacaoadministrativo__unidade_tramitacao_destino',
                  'tramitacaoadministrativo__status']

    def __init__(self, *args, **kwargs):
        super(DocumentoAdministrativoFilterSet, self).__init__(*args, **kwargs)

        local_atual = 'tramitacaoadministrativo__unidade_tramitacao_destino'
        self.filters['tipo'].label = 'Tipo de Documento'
        self.filters['protocolo__numero'].label = 'Núm. Protocolo'
        self.filters['tramitacaoadministrativo__status'].label = 'Situação'
        self.filters[local_atual].label = 'Localização Atual'

        row1 = to_row(
            [('tipo', 8),
             ('o', 4), ])

        row2 = to_row(
            [('numero', 2),
             ('ano', 2),
             ('protocolo__numero', 2),
             ('numero_externo', 2),
             ('data', 4)])

        row3 = to_row(
            [('interessado', 6),
             ('assunto', 6)])

        row4 = to_row(
            [
                ('tramitacao', 2),
                ('tramitacaoadministrativo__status', 5),
                ('tramitacaoadministrativo__unidade_tramitacao_destino', 5),
            ])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar Documento'),
                     row1, row2,
                     row3, row4,
                     form_actions(label='Pesquisar'))
        )


class AnularProcoloAdmForm(ModelForm):

    logger = logging.getLogger(__name__)

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

        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        numero = cleaned_data['numero']
        ano = cleaned_data['ano']

        try:
            self.logger.debug(
                "Tentando obter Protocolo com numero={} e ano={}.".format(numero, ano))
            protocolo = Protocolo.objects.get(numero=numero, ano=ano)
            if protocolo.anulado:
                self.logger.error(
                    "Protocolo %s/%s já encontra-se anulado" % (numero, ano))
                raise forms.ValidationError(
                    _("Protocolo %s/%s já encontra-se anulado")
                    % (numero, ano))
        except ObjectDoesNotExist:
            self.logger.error("Protocolo %s/%s não existe" % (numero, ano))
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
            self.logger.error("Protocolo %s/%s não pode ser removido pois existem "
                              "documentos vinculados a ele." % (numero, ano))
            raise forms.ValidationError(
                _("Protocolo %s/%s não pode ser removido pois existem "
                    "documentos vinculados a ele." % (numero, ano)))

        return cleaned_data

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

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Identificação do Protocolo'),
                     row1,
                     row2,
                     HTML("&nbsp;"),
                     form_actions(label='Anular')
                     )
        )
        super(AnularProcoloAdmForm, self).__init__(
            *args, **kwargs)


class ProtocoloDocumentForm(ModelForm):

    tipo_protocolo = forms.ChoiceField(required=True,
                                       label=_('Tipo de Protocolo'),
                                       choices=TIPOS_PROTOCOLO_CREATE,
                                       initial=0,)

    tipo_documento = forms.ModelChoiceField(
        label=_('Tipo de Documento'),
        required=True,
        queryset=TipoDocumentoAdministrativo.objects.all(),
        empty_label='Selecione',
    )

    numero_paginas = forms.CharField(label=_('Núm. Páginas'), required=True)
    assunto = forms.CharField(
        widget=forms.Textarea, label=_('Assunto'), required=True)

    interessado = forms.CharField(required=True,
                                  label=_('Interessado'))

    observacao = forms.CharField(required=False,
                                 widget=forms.Textarea, label=_('Observação'))

    numero = forms.IntegerField(
        required=False, label=_('Número de Protocolo (opcional)'))

    data_hora_manual = forms.ChoiceField(
        label=_('Informar data e hora manualmente?'),
        widget=forms.RadioSelect(),
        choices=YES_NO_CHOICES,
        initial=False)

    class Meta:
        model = Protocolo
        fields = ['tipo_protocolo',
                  'tipo_documento',
                  'numero_paginas',
                  'assunto',
                  'interessado',
                  'observacao',
                  'numero',
                  'data',
                  'hora',
                  ]

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [(InlineRadios('tipo_protocolo'), 12)])
        row2 = to_row(
            [('tipo_documento', 5),
             ('numero_paginas', 2),
             (Div(), 1),
             (InlineRadios('data_hora_manual'), 4),
             ])
        row3 = to_row([
            (Div(), 2),
            (Alert(
                """
                Usuário: <strong>{}</strong> - {}<br> 
                IP: <strong>{}</strong> - {}<br>
                
                """.format(
                    kwargs['initial']['user_data_hora_manual'],
                    Protocolo._meta.get_field(
                        'user_data_hora_manual').help_text,
                    kwargs['initial']['ip_data_hora_manual'],
                    Protocolo._meta.get_field(
                        'ip_data_hora_manual').help_text,

                ),
                dismiss=False,
                css_class='alert-info'), 6),
            ('data', 2),
            ('hora', 2),
        ])
        row4 = to_row(
            [('assunto', 12)])
        row5 = to_row(
            [('interessado', 12)])
        row6 = to_row(
            [('observacao', 12)])
        row7 = to_row(
            [('numero', 12)])

        fieldset = Fieldset(_('Protocolo com data e hora informados manualmente'),
                            row3,
                            css_id='protocolo_data_hora_manual')

        config = AppConfig.objects.first()
        if not config.protocolo_manual:
            row3 = to_row([(HTML("&nbsp;"), 12)])
            fieldset = row3

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Identificação de Documento'),
                     row1,
                     row2),
                     fieldset,
            row4,
            row5,
            HTML("&nbsp;"),
            Fieldset(_('Número do Protocolo (Apenas se quiser que a numeração comece '
                       'a partir do número a ser informado)'),
                     row7,
                     HTML("&nbsp;"),
                     form_actions(label=_('Protocolar Documento'))
                     )
        )
        super(ProtocoloDocumentForm, self).__init__(
            *args, **kwargs)

        if not config.protocolo_manual:
            self.fields['data_hora_manual'].widget = forms.HiddenInput()



class ProtocoloMateriaForm(ModelForm):

    logger = logging.getLogger(__name__)

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
        empty_label='------',
    )

    numero_materia = forms.CharField(
        label=_('Número matéria'), required=False)

    ano_materia = forms.CharField(
        label=_('Ano matéria'), required=False)

    vincular_materia = forms.ChoiceField(
        label=_('Vincular a matéria existente?'),
        widget=forms.RadioSelect(),
        choices=YES_NO_CHOICES,
        initial=False)

    numero_paginas = forms.CharField(label=_('Núm. Páginas'), required=True)

    observacao = forms.CharField(required=False,
                                 widget=forms.Textarea, label=_('Observação'))

    assunto_ementa = forms.CharField(required=True,
                                     widget=forms.Textarea, label=_('Ementa'))

    numero = forms.IntegerField(
        required=False, label=_('Número de Protocolo (opcional)'))

    data_hora_manual = forms.ChoiceField(
        label=_('Informar data e hora manualmente?'),
        widget=forms.RadioSelect(),
        choices=YES_NO_CHOICES,
        initial=False)

    class Meta:
        model = Protocolo
        fields = ['tipo_materia',
                  'numero_paginas',
                  'autor',
                  'tipo_autor',
                  'assunto_ementa',
                  'observacao',
                  'numero_materia',
                  'ano_materia',
                  'vincular_materia',
                  'numero',
                  'data',
                  'hora',
                  ]

    def clean_autor(self):
        autor_field = self.cleaned_data['autor']
        try:
            self.logger.debug(
                "Tentando obter Autor com id={}.".format(autor_field.id))
            autor = Autor.objects.get(id=autor_field.id)
        except ObjectDoesNotExist:
            self.logger.error(
                "Autor com id={} não encontrado. Definido como None.".format(autor_field.id))
            autor_field = None
        else:
            self.logger.info(
                "Autor com id={} encontrado com sucesso.".format(autor_field.id))
            autor_field = autor
        return autor_field

    def clean(self):
        super(ProtocoloMateriaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data
        if self.is_valid():
            if data['vincular_materia'] == 'True':
                try:
                    if not data['ano_materia'] or not data['numero_materia']:
                        self.logger.error(
                            "Não foram informados o número ou ano da matéria a ser vinculada")
                        raise ValidationError(
                            'Favor informar o número e ano da matéria a ser vinculada')
                    self.logger.debug("Tentando obter MateriaLegislativa com ano={}, numero={} e data={}."
                                      .format(data['ano_materia'], data['numero_materia'], data['tipo_materia']))
                    self.materia = MateriaLegislativa.objects.get(ano=data['ano_materia'],
                                                                  numero=data['numero_materia'],
                                                                  tipo=data['tipo_materia'])
                    if self.materia.numero_protocolo:
                        self.logger.error("MateriaLegislativa informada já possui o protocolo {}/{} vinculado."
                                          .format(self.materia.numero_protocolo, self.materia.ano))
                        raise ValidationError(_('Matéria Legislativa informada já possui o protocolo {}/{} vinculado.'
                                                .format(self.materia.numero_protocolo, self.materia.ano)))
                except ObjectDoesNotExist:
                    self.logger.error("MateriaLegislativa informada (ano={}, numero={} e data={}) não existente."
                                      .format(data['ano_materia'], data['numero_materia'], data['tipo_materia']))
                    raise ValidationError(
                        _('Matéria Legislativa informada não existente.'))

        return data

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [('tipo_materia', 4),
             ('numero_paginas', 2),
             ('tipo_autor', 3),
             ('autor', 3)])
        row2 = to_row(
            [(InlineRadios('vincular_materia'), 3),
             ('numero_materia', 2),
             ('ano_materia', 2),
             (Div(), 1),
             (InlineRadios('data_hora_manual'), 4),
             ])
        row3 = to_row([
            (Div(), 2),
            (Alert(
                """
                Usuário: <strong>{}</strong> - {}<br> 
                IP: <strong>{}</strong> - {}<br>
                
                """.format(
                    kwargs['initial']['user_data_hora_manual'],
                    Protocolo._meta.get_field(
                        'user_data_hora_manual').help_text,
                    kwargs['initial']['ip_data_hora_manual'],
                    Protocolo._meta.get_field(
                        'ip_data_hora_manual').help_text,

                ),
                dismiss=False,
                css_class='alert-info'), 6),
            ('data', 2),
            ('hora', 2),
        ])
        row4 = to_row(
            [('assunto_ementa', 12)])
        row5 = to_row(
            [('observacao', 12)])
        row6 = to_row(
            [('numero', 12)])

        fieldset = Fieldset(_('Protocolo com data e hora informados manualmente'),
                            row3,
                            css_id='protocolo_data_hora_manual')

        config = AppConfig.objects.first()
        if not config.protocolo_manual:
            row3 = to_row([(HTML("&nbsp;"), 12)])
            fieldset = row3

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Identificação da Matéria'),
                     row1,
                     row2),
            fieldset,
            row4,
            row5,
            HTML("&nbsp;"),
            Fieldset(_('Número do Protocolo (Apenas se quiser que a numeração comece'
                       ' a partir do número a ser informado)'),
                     row6,
                     HTML("&nbsp;"),
                     form_actions(label=_('Protocolar Matéria')))
        )

        super(ProtocoloMateriaForm, self).__init__(
            *args, **kwargs)

        if not config.protocolo_manual:
            self.fields['data_hora_manual'].widget = forms.HiddenInput()


class DocumentoAcessorioAdministrativoForm(FileFieldCheckMixin, ModelForm):

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

    logger = logging.getLogger(__name__)

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

        if not self.is_valid():
            return self.cleaned_data

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
                    self.logger.error('A origem da nova tramitação ({}) deve ser  '
                                      'igual ao destino ({}) da última adicionada!'
                                      .format(self.cleaned_data['unidade_tramitacao_local'], destino))
                    msg = _('A origem da nova tramitação deve ser igual ao '
                            'destino  da última adicionada!')
                    raise ValidationError(msg)

            if self.cleaned_data['data_tramitacao'] > timezone.now().date():
                self.logger.error('A data de tramitação ({}) deve ser '
                                  'menor ou igual a data de hoje ({})!'
                                  .format(self.cleaned_data['data_tramitacao'], timezone.now().date()))
                msg = _(
                    'A data de tramitação deve ser ' +
                    'menor ou igual a data de hoje!')
                raise ValidationError(msg)

            if (ultima_tramitacao and
                    data_tram_form < ultima_tramitacao.data_tramitacao):
                self.logger.error('A data da nova tramitação ({}) deve ser '
                                  'maior que a data da última tramitação ({})!'
                                  .format(data_tram_form, ultima_tramitacao.data_tramitacao))
                msg = _('A data da nova tramitação deve ser ' +
                        'maior que a data da última tramitação!')
                raise ValidationError(msg)

        if data_enc_form:
            if data_enc_form < data_tram_form:
                self.logger.error('A data de encaminhamento ({}) deve ser '
                                  'maior que a data de tramitação ({})!'
                                  .format(data_enc_form, data_tram_form))
                msg = _('A data de encaminhamento deve ser ' +
                        'maior que a data de tramitação!')
                raise ValidationError(msg)

        if data_prazo_form:
            if data_prazo_form < data_tram_form:
                self.logger.error('A data fim de prazo ({}) deve ser '
                                  'maior que a data de tramitação ({})!'
                                  .format(data_prazo_form, data_tram_form))
                msg = _('A data fim de prazo deve ser ' +
                        'maior que a data de tramitação!')
                raise ValidationError(msg)

        return self.cleaned_data


class TramitacaoAdmEditForm(TramitacaoAdmForm):

    unidade_tramitacao_local = forms.ModelChoiceField(
        queryset=UnidadeTramitacao.objects.all(),
        widget=forms.HiddenInput())

    data_tramitacao = forms.DateField(widget=forms.HiddenInput())

    logger = logging.getLogger(__name__)

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
        super(TramitacaoAdmEditForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        ultima_tramitacao = TramitacaoAdministrativo.objects.filter(
            documento_id=self.instance.documento_id).order_by(
            '-data_tramitacao',
            '-id').first()

        # Se a Tramitação que está sendo editada não for a mais recente,
        # ela não pode ter seu destino alterado.
        if ultima_tramitacao != self.instance:
            if self.cleaned_data['unidade_tramitacao_destino'] != \
                    self.instance.unidade_tramitacao_destino:
                self.logger.error('Você não pode mudar a Unidade de Destino desta '
                                  'tramitação (id={}), pois irá conflitar com a Unidade '
                                  'Local da tramitação seguinte'.format(self.instance.documento_id))
                raise ValidationError(
                    'Você não pode mudar a Unidade de Destino desta '
                    'tramitação, pois irá conflitar com a Unidade '
                    'Local da tramitação seguinte')

        self.cleaned_data['data_tramitacao'] = \
            self.instance.data_tramitacao
        self.cleaned_data['unidade_tramitacao_local'] = \
            self.instance.unidade_tramitacao_local

        return self.cleaned_data


class AnexadoForm(ModelForm):

    logger = logging.getLogger(__name__)

    tipo = forms.ModelChoiceField(
        label='Tipo',
        required=True,
        queryset=TipoDocumentoAdministrativo.objects.all(),
        empty_label='Selecione'
    )

    numero = forms.CharField(label='Número', required=True)

    ano = forms.CharField(label='Ano', required=True)

    def __init__(self, *args, **kwargs):
        return  super(AnexadoForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(AnexadoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        try:
            self.logger.info(
                "Tentando obter objeto DocumentoAdministrativo (numero={}, ano={}, tipo={})."
                .format(cleaned_data['numero'], cleaned_data['ano'], cleaned_data['tipo'])
            )
            documento_anexado = DocumentoAdministrativo.objects.get(
                numero=cleaned_data['numero'],
                ano=cleaned_data['ano'],
                tipo=cleaned_data['tipo']
            )
        except ObjectDoesNotExist:
            msg = _('O Documento Administrativo a ser anexado (numero={}, ano={}, tipo={}) não existe no cadastro'
                    ' de documentos administrativos.'.format(cleaned_data['numero'], cleaned_data['ano'], cleaned_data['tipo']))
            self.logger.error("O documento a ser anexado não existe no cadastro"
                              " de documentos administrativos")
            raise ValidationError(msg)

        documento_principal = self.instance.documento_principal
        if documento_principal == documento_anexado:
            self.logger.error("O documento não pode ser anexado a si mesmo.")
            raise ValidationError(_("O documento não pode ser anexado a si mesmo"))

        is_anexado = Anexado.objects.filter(documento_principal=documento_principal,
                                            documento_anexado=documento_anexado
                                            ).exists()
        
        if is_anexado:
            self.logger.error("Documento já se encontra anexado.")
            raise ValidationError(_('Documento já se encontra anexado'))

        cleaned_data['documento_anexado'] = documento_anexado

        return cleaned_data

    def save(self, commit=False):
        anexado = super(AnexadoForm, self).save(commit)
        anexado.documento_anexado = self.cleaned_data['documento_anexado']
        anexado.save()
        return anexado

    class Meta:
        model = Anexado
        fields = ['tipo', 'numero', 'ano', 'data_anexacao', 'data_desanexacao']


class AnexadoEmLoteFilterSet(django_filters.FilterSet):

    class Meta(FilterOverridesMetaMixin):
        model = DocumentoAdministrativo
        fields = ['tipo', 'data']

    def __init__(self, *args, **kwargs):
        super(AnexadoEmLoteFilterSet, self).__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Documento'
        self.filters['data'].label = 'Data (Inicial - Final)'
        self.form.fields['tipo'].required = True
        self.form.fields['data'].required = True

        row1 = to_row([('tipo', 12)])
        row2 = to_row([('data', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Documentos'), 
                        row1, row2, form_actions(label='Pesquisar'))
        )


class DocumentoAdministrativoForm(FileFieldCheckMixin, ModelForm):

    logger = logging.getLogger(__name__)

    data = forms.DateField(initial=timezone.now)

    ano_protocolo = forms.ChoiceField(
        required=False,
        label=Protocolo._meta.
        get_field('ano').verbose_name,
        choices=choice_force_optional(choice_anos_com_protocolo),
        widget=forms.Select(
            attrs={'class': 'selector'}))

    numero_protocolo = forms.IntegerField(required=False,
                                          label=Protocolo._meta.
                                          get_field('numero').verbose_name)

    restrito = forms.ChoiceField(label=_('Acesso Restrito'),
                                 widget=forms.RadioSelect(),
                                 choices=YES_NO_CHOICES,
                                 initial=False)

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
                  'numero_externo',
                  'observacao',
                  'texto_integral',
                  'protocolo',
                  'restrito'
                  ]

        widgets = {'protocolo': forms.HiddenInput()}

    def clean(self):
        super(DocumentoAdministrativoForm, self).clean()

        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        numero_protocolo = self.data['numero_protocolo']
        ano_protocolo = self.data['ano_protocolo']
        numero_documento = int(self.cleaned_data['numero'])
        tipo_documento = int(self.data['tipo'])
        ano_documento = int(self.data['ano'])

        # não permite atualizar para numero/ano/tipo existente
        if self.instance.pk:
            mudanca_doc = numero_documento != self.instance.numero \
                or ano_documento != self.instance.ano \
                or tipo_documento != self.instance.tipo.pk

        if not self.instance.pk or mudanca_doc:
            doc_exists = DocumentoAdministrativo.objects.filter(numero=numero_documento,
                                                                tipo=tipo_documento,
                                                                ano=ano_documento).exists()
            if doc_exists:
                self.logger.error("DocumentoAdministrativo (numero={}, tipo={} e ano={}) já existe."
                                  .format(numero_documento, tipo_documento, ano_documento))
                raise ValidationError(_('Documento já existente'))

        # campos opcionais, mas que se informados devem ser válidos
        if numero_protocolo and ano_protocolo:
            try:
                self.logger.debug("Tentando obter Protocolo com numero={} e ano={}."
                                  .format(numero_protocolo, ano_protocolo))
                self.fields['protocolo'].initial = Protocolo.objects.get(
                    numero=numero_protocolo,
                    ano=ano_protocolo).pk
            except ObjectDoesNotExist:
                self.logger.error("Protocolo %s/%s inexistente." % (
                                  numero_protocolo, ano_protocolo))
                msg = _('Protocolo %s/%s inexistente.' % (
                    numero_protocolo, ano_protocolo))
                raise ValidationError(msg)
            except MultipleObjectsReturned:
                self.logger.error("Existe mais de um Protocolo com este ano ({}) e número ({}).".format(
                    ano_protocolo, numero_protocolo))
                msg = _(
                    'Existe mais de um Protocolo com este ano (%s) e número (%s).' % (
                        ano_protocolo, numero_protocolo))
                raise ValidationError(msg)

            inst = self.instance.protocolo
            protocolo_antigo = inst.numero if inst else None

            if str(protocolo_antigo) != numero_protocolo:
                exist_materia = MateriaLegislativa.objects.filter(
                    numero_protocolo=numero_protocolo,
                    ano=ano_protocolo).exists()

                exist_doc = DocumentoAdministrativo.objects.filter(
                    protocolo__numero=numero_protocolo,
                    protocolo__ano=ano_protocolo).exists()
                if exist_materia or exist_doc:
                    self.logger.error('Protocolo com numero=%s e ano=%s já possui'
                                      ' documento vinculado' % (numero_protocolo, ano_protocolo))
                    raise ValidationError(_('Protocolo %s/%s já possui'
                                            ' documento vinculado'
                                            % (numero_protocolo, ano_protocolo)))

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
            [('tipo', 6), ('numero', 3), ('ano', 3)])

        row2 = to_row(
            [('data', 4), ('numero_protocolo', 4), ('ano_protocolo', 4)])

        row3 = to_row(
            [('assunto', 12)])

        row4 = to_row(
            [('interessado', 7), ('tramitacao', 2), (InlineRadios('restrito'), 3)])

        row5 = to_row(
            [('texto_integral', 12)])

        row6 = to_row(
            [('numero_externo', 4), ('dias_prazo', 6), ('data_fim_prazo', 2)])

        row7 = to_row(
            [('observacao', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2, row3, row4, row5),
            Fieldset(_('Outras Informações'),
                     row6, row7))
        super(DocumentoAdministrativoForm, self).__init__(
            *args, **kwargs)


class DesvincularDocumentoForm(ModelForm):

    logger = logging.getLogger(__name__)

    numero = forms.CharField(
        required=True,
        label=DocumentoAdministrativo._meta.get_field('numero').verbose_name)

    ano = forms.ChoiceField(
        required=True,
        label=DocumentoAdministrativo._meta.get_field('ano').verbose_name,
        choices=choice_anos_com_documentoadministrativo,
        widget=forms.Select(attrs={'class': 'selector'}))

    def clean(self):
        super(DesvincularDocumentoForm, self).clean()

        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        numero = cleaned_data['numero']
        ano = cleaned_data['ano']
        tipo = cleaned_data['tipo']

        try:
            self.logger.debug("Tentando obter DocumentoAdministrativo com numero={}, ano={} e tipo={}."
                              .format(numero, ano, tipo))
            documento = DocumentoAdministrativo.objects.get(
                numero=numero, ano=ano, tipo=tipo)
            if not documento.protocolo:
                self.logger.error(
                    "DocumentoAdministrativo %s %s/%s não se encontra vinculado a nenhum protocolo." % (tipo, numero, ano))
                raise forms.ValidationError(
                    _("%s %s/%s não se encontra vinculado a nenhum protocolo" % (tipo, numero, ano)))
        except ObjectDoesNotExist:
            self.logger.error(
                "DocumentoAdministrativo %s %s/%s não existe" % (tipo, numero, ano))
            raise forms.ValidationError(
                _("%s %s/%s não existe" % (tipo, numero, ano)))

        return cleaned_data

    class Meta:
        model = DocumentoAdministrativo
        fields = ['tipo',
                  'numero',
                  'ano',
                  ]

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [('numero', 4),
             ('ano', 4),
             ('tipo', 4)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Identificação do Documento'),
                     row1,
                     HTML("&nbsp;"),
                     form_actions(label='Desvincular')
                     )
        )
        super(DesvincularDocumentoForm, self).__init__(
            *args, **kwargs)


class DesvincularMateriaForm(forms.Form):

    logger = logging.getLogger(__name__)

    numero = forms.CharField(required=True,
                             label=_('Número da Matéria'))
    ano = forms.ChoiceField(required=True,
                            label=_('Ano da Matéria'),
                            choices=choice_anos_com_materias,
                            widget=forms.Select(attrs={'class': 'selector'}))
    tipo = forms.ModelChoiceField(label=_('Tipo de Matéria'),
                                  required=True,
                                  queryset=TipoMateriaLegislativa.objects.all(),
                                  empty_label='------')

    def clean(self):
        super(DesvincularMateriaForm, self).clean()

        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        numero = cleaned_data['numero']
        ano = cleaned_data['ano']
        tipo = cleaned_data['tipo']

        try:
            self.logger.info("Tentando obter MateriaLegislativa com numero={}, ano={} e tipo={}."
                             .format(numero, ano, tipo))
            materia = MateriaLegislativa.objects.get(
                numero=numero, ano=ano, tipo=tipo)
            if not materia.numero_protocolo:
                self.logger.error(
                    "MateriaLegislativa %s %s/%s não se encontra vinculada a nenhum protocolo" % (tipo, numero, ano))
                raise forms.ValidationError(
                    _("%s %s/%s não se encontra vinculada a nenhum protocolo" % (tipo, numero, ano)))
        except ObjectDoesNotExist:
            self.logger.error(
                "MateriaLegislativa %s %s/%s não existe" % (tipo, numero, ano))
            raise forms.ValidationError(
                _("%s %s/%s não existe" % (tipo, numero, ano)))

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(DesvincularMateriaForm, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('numero', 4),
             ('ano', 4),
             ('tipo', 4)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Identificação da Matéria'),
                     row1,
                     HTML("&nbsp;"),
                     form_actions(label='Desvincular')
                     )
        )


def pega_ultima_tramitacao_adm():
    return TramitacaoAdministrativo.objects.values(
        'documento_id').annotate(data_encaminhamento=Max(
            'data_encaminhamento'),
        id=Max('id')).values_list('id', flat=True)


def filtra_tramitacao_adm_status(status):
    lista = pega_ultima_tramitacao_adm()
    return TramitacaoAdministrativo.objects.filter(
        id__in=lista,
        status=status).distinct().values_list('materia_id', flat=True)


def filtra_tramitacao_adm_destino(destino):
    lista = pega_ultima_tramitacao_adm()
    return TramitacaoAdministrativo.objects.filter(
        id__in=lista,
        unidade_tramitacao_destino=destino).distinct().values_list(
            'documento_id', flat=True)


def filtra_tramitacao_adm_destino_and_status(status, destino):
    lista = pega_ultima_tramitacao_adm()
    return TramitacaoAdministrativo.objects.filter(
        id__in=lista,
        status=status,
        unidade_tramitacao_destino=destino).distinct().values_list(
            'documento_id', flat=True)


class FichaPesquisaAdmForm(forms.Form):

    logger = logging.getLogger(__name__)

    tipo_documento = forms.ModelChoiceField(
        label=TipoDocumentoAdministrativo._meta.verbose_name,
        queryset=TipoDocumentoAdministrativo.objects.all(),
        empty_label='Selecione')

    data_inicial = forms.DateField(
        label='Data Inicial',
        widget=forms.DateInput(format='%d/%m/%Y')
    )

    data_final = forms.DateField(
        label='Data Final',
        widget=forms.DateInput(format='%d/%m/%Y')
    )

    def __init__(self, *args, **kwargs):
        super(FichaPesquisaAdmForm, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('tipo_documento', 6),
             ('data_inicial', 3),
             ('data_final', 3)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(
                ('Formulário de Ficha'),
                row1,
                form_actions(label='Pesquisar')
            )
        )

    def clean(self):
        super(FichaPesquisaAdmForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        if cleaned_data['data_final'] < cleaned_data['data_inicial']:
            self.logger.error("A Data Final ({}) não pode ser menor que a Data Inicial ({})."
                              .format(cleaned_data['data_final'], cleaned_data['data_inicial']))
            raise ValidationError(_(
                'A Data Final não pode ser menor que a Data Inicial'))

        return cleaned_data


class FichaSelecionaAdmForm(forms.Form):
    documento = forms.ModelChoiceField(
        widget=forms.RadioSelect,
        queryset=DocumentoAdministrativo.objects.all(),
        label='')

    def __init__(self, *args, **kwargs):
        super(FichaSelecionaAdmForm, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('documento', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(
                ('Selecione a ficha que deseja imprimir'),
                row1,
                form_actions(label='Gerar Impresso')
            )
        )
