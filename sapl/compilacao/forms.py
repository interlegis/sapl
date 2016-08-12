from datetime import timedelta

from crispy_forms.bootstrap import (Alert, FieldWithButtons, FormActions,
                                    InlineRadios, StrictButton)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (HTML, Button, Column, Div, Field, Fieldset,
                                 Layout, Row, Submit)
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db.models import Q
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _

from sapl import utils
from sapl.compilacao.models import (NOTAS_PUBLICIDADE_CHOICES,
                                    PARTICIPACAO_SOCIAL_CHOICES, Dispositivo,
                                    Nota, Publicacao, TextoArticulado,
                                    TipoDispositivo, TipoNota, TipoPublicacao,
                                    TipoTextoArticulado, TipoVide,
                                    VeiculoPublicacao, Vide)
from sapl.compilacao.utils import DISPOSITIVO_SELECT_RELATED
from sapl.crispy_layout_mixin import SaplFormLayout, to_column, to_row
from sapl.utils import YES_NO_CHOICES

error_messages = {
    'required': _('Este campo é obrigatório'),
    'invalid': _('URL inválida.')
}

ta_error_messages = {
    'required': _('Este campo é obrigatório'),
}


class TipoTaForm(ModelForm):
    sigla = forms.CharField(
        label=TipoTextoArticulado._meta.get_field(
            'sigla').verbose_name)
    descricao = forms.CharField(
        label=TipoTextoArticulado._meta.get_field(
            'descricao').verbose_name)

    participacao_social = forms.NullBooleanField(
        label=TipoTextoArticulado._meta.get_field(
            'participacao_social').verbose_name,
        widget=forms.Select(choices=YES_NO_CHOICES),
        required=True)

    class Meta:
        model = TipoTextoArticulado
        fields = ['sigla',
                  'descricao',
                  'content_type',
                  'participacao_social',
                  ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('sigla', 2),
            ('descricao', 4),
            ('content_type', 3),
            ('participacao_social', 3),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, css_class="col-md-12"))
        super(TipoTaForm, self).__init__(*args, **kwargs)


class TaForm(ModelForm):
    tipo_ta = forms.ModelChoiceField(
        label=TipoTextoArticulado._meta.verbose_name,
        queryset=TipoTextoArticulado.objects.all(),
        required=True,
        empty_label=None)
    numero = forms.IntegerField(
        label=TextoArticulado._meta.get_field(
            'numero').verbose_name,
        required=True)
    ano = forms.IntegerField(
        label=TextoArticulado._meta.get_field(
            'ano').verbose_name,
        required=True)

    data = forms.DateField(
        label=TextoArticulado._meta.get_field(
            'data').verbose_name,
        input_formats=['%d/%m/%Y'],
        required=True,
        widget=forms.DateInput(
            format='%d/%m/%Y'),
        error_messages=ta_error_messages
    )
    ementa = forms.CharField(
        label='',
        widget=forms.Textarea,
        error_messages=ta_error_messages)
    observacao = forms.CharField(
        label='',
        widget=forms.Textarea,
        error_messages=ta_error_messages,
        required=False)
    participacao_social = forms.NullBooleanField(
        label=TextoArticulado._meta.get_field(
            'participacao_social').verbose_name,
        widget=forms.Select(choices=PARTICIPACAO_SOCIAL_CHOICES),
        required=False)

    class Meta:
        model = TextoArticulado
        fields = ['tipo_ta',
                  'numero',
                  'ano',
                  'data',
                  'ementa',
                  'observacao',
                  'participacao_social',
                  ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('tipo_ta', 3),
            ('numero', 2),
            ('ano', 2),
            ('data', 2),
            ('participacao_social', 3),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'), row1, css_class="col-md-12"),
            Fieldset(
                TextoArticulado._meta.get_field('ementa').verbose_name,
                Column('ementa'), css_class="col-md-12"),
            Fieldset(
                TextoArticulado._meta.get_field('observacao').verbose_name,
                Column('observacao'), css_class="col-md-12"),

        )

        super(TaForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['tipo_ta'].widget.attrs['disabled'] = True
            self.fields['tipo_ta'].required = False

    def clean_tipo_ta(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.tipo_ta
        else:
            return self.cleaned_data['tipo_ta']


class NotaForm(ModelForm):

    titulo = forms.CharField(
        label=Nota._meta.get_field('titulo').verbose_name, required=False)
    texto = forms.CharField(
        label=Nota._meta.get_field('texto').verbose_name,
        widget=forms.Textarea,
        error_messages=error_messages)
    url_externa = forms.URLField(
        label=Nota._meta.get_field('url_externa').verbose_name,
        required=False,
        error_messages=error_messages)
    publicidade = forms.ChoiceField(
        required=True,
        label=Nota._meta.get_field('publicidade').verbose_name,
        choices=NOTAS_PUBLICIDADE_CHOICES,
        widget=forms.Select(attrs={'class': 'selector'}))

    tipo = forms.ModelChoiceField(
        label=Nota._meta.get_field('tipo').verbose_name,
        queryset=TipoNota.objects.all(),
        empty_label=None)

    publicacao = forms.DateField(
        label=Nota._meta.get_field('publicacao').verbose_name,
        input_formats=['%d/%m/%Y'],
        required=True,
        widget=forms.DateInput(
            format='%d/%m/%Y'),
        error_messages=error_messages
    )
    efetividade = forms.DateField(
        label=Nota._meta.get_field('efetividade').verbose_name,
        input_formats=['%d/%m/%Y'],
        required=True,
        widget=forms.DateInput(
            format='%d/%m/%Y'),
        error_messages=error_messages)
    dispositivo = forms.ModelChoiceField(queryset=Dispositivo.objects.all(),
                                         widget=forms.HiddenInput())
    pk = forms.IntegerField(widget=forms.HiddenInput(),
                            required=False)

    class Meta:
        model = Nota
        fields = ['titulo',
                  'texto',
                  'url_externa',
                  'publicidade',
                  'publicacao',
                  'efetividade',
                  'tipo',
                  'dispositivo',
                  'pk'
                  ]

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('tipo', 4),
        ])
        row1.append(
            Column(
                Field(
                    'titulo',
                    placeholder=_('Título da Nota (opcional)')
                ),
                css_class='col-md-8'))

        row3 = to_row([
            ('publicidade', 6),
            ('publicacao', 3),
            ('efetividade', 3),
        ])

        buttons = FormActions(
            HTML('<a class="btn btn-inverse btn-close-container">'
                 '%s</a>' % _('Cancelar')),
            Button(
                'submit-form',
                'Salvar',
                css_class='btn btn-primary pull-right')
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(

            Div(
                Div(HTML(_('Notas')), css_class='panel-heading'),
                Div(
                    row1,
                    to_row([(Field(
                        'texto',
                        placeholder=_('Adicionar Nota')), 12)]),
                    to_row([(Field(
                        'url_externa',
                        placeholder=_('URL Externa (opcional)')), 12)]),
                    row3,
                    to_row([(buttons, 12)]),
                    css_class="panel-body"
                ),
                css_class="panel panel-primary"
            )
        )

        super(NotaForm, self).__init__(*args, **kwargs)


class VideForm(ModelForm):
    dispositivo_base = forms.ModelChoiceField(
        queryset=Dispositivo.objects.all(),
        widget=forms.HiddenInput())

    dispositivo_ref = forms.ModelChoiceField(
        label=Vide._meta.get_field(
            'dispositivo_ref').verbose_name,
        queryset=Dispositivo.objects.all())

    tipo = forms.ModelChoiceField(
        label=TipoVide._meta.verbose_name,
        queryset=TipoVide.objects.all(),
        required=True,
        error_messages=error_messages)
    texto = forms.CharField(
        required=False,
        label=Vide._meta.get_field(
            'texto').verbose_name,
        widget=forms.Textarea())

    pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Vide
        fields = ['dispositivo_base',
                  'dispositivo_ref',
                  'texto',
                  'tipo',
                  'pk']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together':
                _("Ja existe um Vide deste tipo para o Dispositivo Referido "),
            }
        }

    def __init__(self, *args, **kwargs):

        buttons = FormActions(
            HTML('<a class="btn btn-inverse btn-close-container">'
                 '%s</a>' % _('Cancelar')),
            Button(
                'submit-form',
                'Salvar',
                css_class='btn-primary pull-right')
        )

        dispositivo_ref = Field(
            'dispositivo_ref',
            data_sapl_ta='DispositivoSearch',
            data_field='dispositivo_ref',
            data_type_selection='radio',
            template="compilacao/layout/dispositivo_radio.html")

        fields_form = []
        fields_form.append(Div(
            Row(to_column((Field(
                'tipo',
                placeholder=_('Selecione um Tipo de Vide')), 12))),
            Row(to_column((dispositivo_ref, 12))),
            Row(to_column((buttons, 12)))))

        fields_form.append(Div(
            Row(to_column((Field(
                'texto',
                placeholder=_('Texto Adicional ao Vide')), 12)))))

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(HTML(_('Vides')), css_class='panel-heading'),
                Div(
                    to_column((fields_form[0], 6)),
                    to_column((fields_form[1], 6)),
                    css_class="panel-body"
                ),
                css_class="panel panel-primary"
            )
        )

        super(VideForm, self).__init__(*args, **kwargs)

        self.fields['dispositivo_ref'].choices = []
        if self.instance and self.instance.dispositivo_ref_id:
            self.fields['dispositivo_ref'].choices = [
                (self.instance.dispositivo_ref.pk,
                 self.instance.dispositivo_ref)]


class PublicacaoForm(ModelForm):

    tipo_publicacao = forms.ModelChoiceField(
        label=TipoPublicacao._meta.verbose_name,
        queryset=TipoPublicacao.objects.all())

    veiculo_publicacao = forms.ModelChoiceField(
        label=VeiculoPublicacao._meta.verbose_name,
        queryset=VeiculoPublicacao.objects.all())

    url_externa = forms.CharField(
        label=Publicacao._meta.get_field('url_externa').verbose_name,
        required=False)

    data = forms.DateField(
        label=Publicacao._meta.get_field('data').verbose_name,
        input_formats=['%d/%m/%Y'],
        required=True,
        widget=forms.DateInput(
            format='%d/%m/%Y'),
        error_messages=error_messages
    )
    hora = forms.TimeField(
        label=Publicacao._meta.get_field('hora').verbose_name,
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'hora_hms'}))
    numero = forms.IntegerField(
        label=Publicacao._meta.get_field(
            'numero').verbose_name,
        required=False)
    ano = forms.IntegerField(
        label=Publicacao._meta.get_field(
            'ano').verbose_name)
    edicao = forms.IntegerField(
        label=Publicacao._meta.get_field(
            'edicao').verbose_name,
        required=False)
    pagina_inicio = forms.IntegerField(
        label=Publicacao._meta.get_field(
            'pagina_inicio').verbose_name,
        required=False)
    pagina_fim = forms.IntegerField(
        label=Publicacao._meta.get_field(
            'pagina_fim').verbose_name,
        required=False)
    ta = forms.ModelChoiceField(queryset=TextoArticulado.objects.all(),
                                widget=forms.HiddenInput())

    class Meta:
        model = Publicacao
        fields = ['tipo_publicacao',
                  'veiculo_publicacao',
                  'url_externa',
                  'data',
                  'hora',
                  'numero',
                  'ano',
                  'edicao',
                  'pagina_inicio',
                  'pagina_fim',
                  'ta']

    def __init__(self, *args, **kwargs):

        row1 = to_row([
            ('tipo_publicacao', 4),
            ('veiculo_publicacao', 6),
            ('ano', 2),
        ])

        row2 = to_row([
            ('data', 4),
            ('hora', 4),
            ('numero', 2),
            ('edicao', 2),
        ])

        row3 = to_row([
            ('pagina_inicio', 2),
            ('pagina_fim', 2),
            ('url_externa', 8),
        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(Publicacao._meta.verbose_name,
                     row1, row2, row3, css_class="col-md-12"))

        super(PublicacaoForm, self).__init__(*args, **kwargs)
        pass


class DispositivoIntegerField(forms.IntegerField):

    def __init__(self, field_name=None, *args, **kwargs):

        if 'required' not in kwargs:
            kwargs.setdefault('required', False)

        self.widget = forms.NumberInput(
            attrs={'title': Dispositivo._meta.get_field(
                field_name).verbose_name,
                'onchange': 'atualizaRotulo()'})

        super(DispositivoIntegerField, self).__init__(
            min_value=0, *args, **kwargs)


class DispositivoEdicaoBasicaForm(ModelForm):

    class Meta:
        model = Dispositivo
        fields = []

        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together':
                _("Já existe um Dispositivo com características idênticas."),
            }
        }

    def __init__(self, *args, **kwargs):

        layout = []

        inst = kwargs['instance'] if 'instance' in kwargs else None

        editor_type = kwargs['initial']['editor_type']\
            if'editor_type' in kwargs['initial'] else ''

        if inst and inst.tipo_dispositivo.formato_variacao0 in [
                TipoDispositivo.FNC8, TipoDispositivo.FNCN]:
            # remove edição do rótulo se o tipo de disp. for não numerável
            if 'rotulo' in DispositivoEdicaoBasicaForm.Meta.fields:
                DispositivoEdicaoBasicaForm.Meta.fields.remove('rotulo')
                for i in range(6):
                    DispositivoEdicaoBasicaForm.Meta.fields.remove(
                        'dispositivo%s' % i)
        elif editor_type == 'get_form_base':
            # remove edição do rótulo se a req do form vier do editor dinamico
            if 'rotulo' in DispositivoEdicaoBasicaForm.Meta.fields:
                DispositivoEdicaoBasicaForm.Meta.fields.remove('rotulo')
                for i in range(6):
                    DispositivoEdicaoBasicaForm.Meta.fields.remove(
                        'dispositivo%s' % i)
        else:
            # adiciona campos de rótulo no formulário
            if 'rotulo' not in DispositivoEdicaoBasicaForm.Meta.fields:
                DispositivoEdicaoBasicaForm.Meta.fields.append('rotulo')
                for i in range(6):
                    DispositivoEdicaoBasicaForm.Meta.fields.append(
                        'dispositivo%s' % i)
            self.dispositivo0 = forms.IntegerField(
                min_value=0,
                label=Dispositivo._meta.get_field('dispositivo0').verbose_name,
                widget=forms.NumberInput(
                    attrs={'title': _('Valor 0(zero) é permitido apenas para '
                                      'Dispositivos com tipos variáveis.'),
                           'onchange': 'atualizaRotulo()'}))
            self.dispositivo1 = DispositivoIntegerField(
                label=('1&ordf; %s' % _('Variação')),
                field_name='dispositivo1')
            self.dispositivo2 = DispositivoIntegerField(
                label=('2&ordf;'),
                field_name='dispositivo2')
            self.dispositivo3 = DispositivoIntegerField(
                label=('3&ordf;'),
                field_name='dispositivo3')
            self.dispositivo4 = DispositivoIntegerField(
                label=('4&ordf;'),
                field_name='dispositivo4')
            self.dispositivo5 = DispositivoIntegerField(
                label=('5&ordf;'),
                field_name='dispositivo5')

            self.rotulo = forms.CharField(
                required=False, label=_('Rótulo Resultante'))

            rotulo_fieldset = to_row([
                ('dispositivo0', 3),
                ('dispositivo1', 2),
                ('dispositivo2', 1),
                ('dispositivo3', 1),
                ('dispositivo4', 1),
                ('dispositivo5', 1),
                ('rotulo', 3)])

            layout.append(Fieldset(_('Construção do Rótulo'), rotulo_fieldset,
                                   css_class="col-md-12"))

        if inst and inst.tipo_dispositivo.dispositivo_de_articulacao:
            if 'texto' in DispositivoEdicaoBasicaForm.Meta.fields:
                DispositivoEdicaoBasicaForm.Meta.fields.remove('texto')
        else:
            if 'texto' not in DispositivoEdicaoBasicaForm.Meta.fields:
                DispositivoEdicaoBasicaForm.Meta.fields.append('texto')

            self.texto = forms.CharField(required=False,
                                         label='',
                                         widget=forms.Textarea())
            row_texto = to_row([('texto', 12)])
            layout.append(
                Fieldset(Dispositivo._meta.get_field('texto').verbose_name,
                         row_texto,
                         css_class="col-md-12"))

        if editor_type == 'get_form_base' and inst.dispositivo_atualizador_id:
            if inst and inst.tipo_dispositivo.dispositivo_de_articulacao:
                if 'texto_atualizador' in\
                        DispositivoEdicaoBasicaForm.Meta.fields:
                    DispositivoEdicaoBasicaForm.Meta.fields.remove(
                        'texto_atualizador')
                    DispositivoEdicaoBasicaForm.Meta.fields.remove(
                        'visibilidade')
            else:
                if 'texto_atualizador' not in\
                        DispositivoEdicaoBasicaForm.Meta.fields:
                    DispositivoEdicaoBasicaForm.Meta.fields.append(
                        'texto_atualizador')
                    DispositivoEdicaoBasicaForm.Meta.fields.append(
                        'visibilidade')

                self.texto_atualizador = forms.CharField(
                    required=False,
                    label='',
                    widget=forms.Textarea(),
                    help_text=_('Não havendo diferenças gráficas entre o '
                                'conteúdo que deve estar no Texto Original e '
                                'no Texto Alterador, não há necessidade '
                                'de duplicar a informação. A validação dos '
                                'dados negará a igualdade.'))
                self.visibilidade = forms.ChoiceField(
                    label=Dispositivo._meta.get_field(
                        'visibilidade').verbose_name,
                    choices=utils.YES_NO_CHOICES,
                    widget=forms.RadioSelect())

                layout.append(
                    Fieldset(Dispositivo._meta.get_field(
                        'texto_atualizador').verbose_name,
                        to_row([(InlineRadios('visibilidade'), 12)]),
                        to_row([('texto_atualizador', 12)]),
                        css_class="col-md-12"))
        else:
            if 'texto_atualizador' in\
                    DispositivoEdicaoBasicaForm.Meta.fields:
                DispositivoEdicaoBasicaForm.Meta.fields.remove(
                    'texto_atualizador')
                DispositivoEdicaoBasicaForm.Meta.fields.remove(
                    'visibilidade')

        fields = DispositivoEdicaoBasicaForm.Meta.fields
        if fields:
            self.base_fields.clear()
            for f in fields:
                self.base_fields.update({f: getattr(self, f)})

        self.helper = FormHelper()

        if not editor_type:
            label_cancel = _('Ir para o Editor Sequencial')
            self.helper.layout = SaplFormLayout(
                *layout, label_cancel=label_cancel)

        elif editor_type == "get_form_base":
            getattr(self, "actions_" + editor_type)(layout, inst)

        super(DispositivoEdicaoBasicaForm, self).__init__(*args, **kwargs)

    def actions_get_form_base(self, layout, inst):
        label_cancel = _('Fechar')

        more = [
            HTML('<a class="btn btn-inverse btn-fechar">%s</a>' %
                 label_cancel),
        ]

        btns_excluir = []

        if not inst.is_relative_auto_insert():
            btns_excluir = [
                HTML('<a class="btn btn-danger btn-action btn-excluir" '
                     'action="json_delete_item_dispositivo" '
                     'title="%s"'
                     '>%s</a>' % (_('Excluir apenas este dispositivo.'),
                                  _('Excluir Dispositivo')))]

            if inst.dispositivos_filhos_set.exists():
                btns_excluir.append(
                    HTML(
                        '<a class="btn btn-danger btn-action btn-excluir" '
                        'action="json_delete_bloco_dispositivo" '
                        'title="%s"'
                        '>%s</a>' % (_('Excluir este dispositivo '
                                       'e toda sua estrutura.'),
                                     _('Excluir Bloco de Dispositivo.'))))

        if btns_excluir:
            css_class = 'btn-group pull-right btns-excluir'
            more.append(Div(*btns_excluir, css_class=css_class))

        if not inst.tipo_dispositivo.dispositivo_de_articulacao:
            more.append(Submit('salvar', _('Salvar'), css_class='pull-right'))

        buttons = FormActions(*more, css_class='form-group')

        _fields = [Div(*layout, css_class="row-fluid")] + \
            [to_row([(buttons, 12)])]
        self.helper.layout = Layout(*_fields)


class DispositivoSearchModalForm(Form):

    tipo_ta = forms.ModelChoiceField(
        label=_('Tipo do Texto Articulado'),
        queryset=TipoTextoArticulado.objects.all(),
        required=False)

    tipo_model = forms.ChoiceField(
        choices=[],
        label=_('Tipos de...'), required=False)

    num_ta = forms.IntegerField(
        label=_('Número do Documento'), required=False)
    ano_ta = forms.IntegerField(
        label=_('Ano do Documento'), required=False)

    dispositivos_internos = forms.ChoiceField(
        label=_('Dispositivos Internos?'),
        choices=utils.YES_NO_CHOICES,
        widget=forms.RadioSelect(),
        required=False)

    max_results = forms.ChoiceField(
        label=_('Limite de Listagem'),
        choices=[(10, _('Dez Dispositivos')),
                 (30, _('Trinta Dispositivos')),
                 (50, _('Cinquenta Dispositivos')),
                 (0, _('Tudo que atender aos Critérios da Busca'))],
        widget=forms.Select(),
        required=False)

    rotulo_dispositivo = forms.CharField(
        label=_('Rótulo'),
        required=False)

    texto_dispositivo = forms.CharField(
        label=_('Pesquisa Textual'),
        required=False)

    def __init__(self, *args, **kwargs):

        fields_search = Fieldset(
            _('Busca por um Dispositivo'),
            Row(
                to_column(('num_ta', 4)),
                to_column(('ano_ta', 4)),
                to_column(('max_results', 4))),
            Row(
                to_column(('tipo_ta', 6)),
                to_column(('tipo_model', 6))),
            Row(to_column((InlineRadios('dispositivos_internos'), 3)),
                to_column(('rotulo_dispositivo', 2)),
                to_column((FieldWithButtons(
                    Field(
                        'texto_dispositivo',
                        placeholder=_('Digite palavras, letras, '
                                      'números ou algo'
                                      ' que estejam no texto.')),
                    StrictButton(_('Buscar'), css_class='btn-busca btn-primary')), 7))
                )
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            fields_search,
            Row(to_column((Div(css_class='result-busca-dispositivo'), 12))))

        if 'choice_model_type_foreignkey_in_extenal_views' in kwargs:
            ch = kwargs.pop('choice_model_type_foreignkey_in_extenal_views')
            if 'data' in kwargs:
                choice = ch(kwargs['data']['tipo_ta'])
                self.base_fields['tipo_model'].choices = choice
            elif 'instance' in kwargs and\
                    isinstance(kwargs['instance'], Dispositivo):
                choice = ch(kwargs['instance'].ta.tipo_ta_id)
                self.base_fields['tipo_model'].choices = choice

        kwargs['initial'].update({'dispositivos_internos': False})
        super(DispositivoSearchModalForm, self).__init__(*args, **kwargs)


class DispositivoEdicaoVigenciaForm(ModelForm):
    inconstitucionalidade = forms.ChoiceField(
        label=Dispositivo._meta.get_field(
            'inconstitucionalidade').verbose_name,
        choices=utils.YES_NO_CHOICES,
        widget=forms.RadioSelect())

    dispositivo_vigencia = forms.ModelChoiceField(
        label=Dispositivo._meta.get_field(
            'dispositivo_vigencia').verbose_name,
        required=False,
        queryset=Dispositivo.objects.all())

    extensao = forms.ChoiceField(
        label=_('Extender a seleção abaixo como Dispositivo de Vigência '
                'para todos dependentes originais '
                'deste Dispositivo em edição?'),
        choices=utils.YES_NO_CHOICES,
        widget=forms.RadioSelect(),
        required=False)

    class Meta:
        model = Dispositivo
        fields = ['inicio_vigencia',
                  'fim_vigencia',
                  'inicio_eficacia',
                  'fim_eficacia',
                  'publicacao',
                  'inconstitucionalidade',
                  'dispositivo_vigencia'
                  ]

        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together':
                _("Já existe um Dispositivo com características idênticas."),
            }
        }

    def __init__(self, *args, **kwargs):

        layout = []

        row_publicacao = to_row([
            ('publicacao', 6),
            (InlineRadios('inconstitucionalidade'), 3), ])
        row_publicacao.fields.append(
            Alert(
                css_class='alert-info col-md-3',
                content='<strong>%s</strong> %s' % (
                    _('Dica!'), _('Inclua uma Nota de Dispositivo informando '
                                  'sobre a Inconstitucionalidade.'))))
        layout.append(
            Fieldset(_('Registro de Publicação e Validade'),
                     row_publicacao,
                     css_class="col-md-12"))

        row_datas = to_row([
            ('inicio_vigencia', 3),
            ('fim_vigencia', 3),
            ('inicio_eficacia', 3),
            ('fim_eficacia', 3), ])
        layout.append(
            Fieldset(_('Datas de Controle de Vigência'),
                     row_datas,
                     css_class="col-md-12"))

        row_vigencia = Field(
            'dispositivo_vigencia',
            data_sapl_ta='DispositivoSearch',
            data_field='dispositivo_vigencia',
            data_type_selection='radio',
            template="compilacao/layout/dispositivo_radio.html")
        layout.append(
            Fieldset(_('Dispositivo de Vigência'),
                     to_row([(InlineRadios('extensao'), 12)]),
                     row_vigencia,
                     css_class="col-md-12"))

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            *layout,
            label_cancel=_('Ir para o Editor Sequencial'))

        super(DispositivoEdicaoVigenciaForm, self).__init__(*args, **kwargs)

        pubs = Publicacao.objects.order_by(
            '-data', '-hora').filter(Q(ta=self.instance.ta) |
                                     Q(ta=self.instance.ta_publicado))
        self.fields['publicacao'].choices = [("", "---------")] + [(
            p.pk, _('%s realizada em %s. %s') % (
                p.tipo_publicacao,
                defaultfilters.date(
                    p.data, "d \d\e F \d\e Y"),
                str(p.ta))) for p in pubs]

        dvs = Dispositivo.objects.order_by('ordem').filter(
            pk=self.instance.dispositivo_vigencia_id)
        self.fields['dispositivo_vigencia'].choices = [(d.pk, d) for d in dvs]

    def clean_dispositivo_vigencia(self):
        dv = self.cleaned_data['dispositivo_vigencia']

        if dv and dv.is_relative_auto_insert():
            dv = dv.dispositivo_pai

        return dv

    def save(self):
        super(DispositivoEdicaoVigenciaForm, self).save()

        data = self.cleaned_data

        extensao = 'extensao' in data and data['extensao'] == 'True'

        if extensao:
            dv = data['dispositivo_vigencia']

            if dv and dv.is_relative_auto_insert():
                dv = dv.dispositivo_pai

            dv_pk = dv.pk if dv else None
            instance = self.instance

            def extenderPara(dpt_pk):

                Dispositivo.objects.filter(
                    dispositivo_pai_id=dpt_pk,
                    ta_publicado__isnull=True).update(
                    dispositivo_vigencia_id=dv_pk)

                filhos = Dispositivo.objects.filter(
                    dispositivo_pai_id=dpt_pk).values_list('pk', flat=True)

                for d in filhos:
                    extenderPara(d)

            extenderPara(instance.pk)


class MultipleChoiceWithoutValidationField(forms.MultipleChoiceField):

    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'], code='required')


class DispositivoDefinidorVigenciaForm(Form):

    dispositivo_vigencia = MultipleChoiceWithoutValidationField(
        label=Dispositivo._meta.get_field(
            'dispositivo_vigencia').verbose_name,
        required=False)

    def __init__(self, *args, **kwargs):

        layout = []

        row_vigencia = Field(
            'dispositivo_vigencia',
            data_sapl_ta='DispositivoSearch',
            data_field='dispositivo_vigencia',
            data_type_selection='checkbox',
            template="compilacao/layout/dispositivo_checkbox.html")
        layout.append(
            Fieldset(_('Definidor de Vigência dos Dispositívos abaixo'),
                     row_vigencia,
                     css_class="col-md-12"))

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            *layout,
            label_cancel=_('Ir para o Editor Sequencial'))

        pk = kwargs.pop('pk')
        super(DispositivoDefinidorVigenciaForm, self).__init__(*args, **kwargs)

        dvs = Dispositivo.objects.order_by('ta', 'ordem').filter(
            dispositivo_vigencia_id=pk).select_related(
            *DISPOSITIVO_SELECT_RELATED)
        self.initial['dispositivo_vigencia'] = [d.pk for d in dvs]

        TA_TA_PUB = 'ta_id', 'ta_publicado_id'
        tas = Dispositivo.objects.order_by(
            *TA_TA_PUB).filter(dispositivo_vigencia_id=pk).distinct(
            *TA_TA_PUB).values_list(
            *TA_TA_PUB)

        tas = list(set().union(*list(map(list, zip(*tas)))))

        if not tas:
            tas = Dispositivo.objects.filter(pk=pk).values_list('ta_id')

        dvs = Dispositivo.objects.order_by(
            '-ta__data', '-ta__ano', '-ta__numero', 'ta', 'ordem').filter(
            ta__in=tas).select_related(*DISPOSITIVO_SELECT_RELATED)
        self.fields['dispositivo_vigencia'].choices = [
            (d.pk, d)
            for d in dvs
            if d.pk in self.initial['dispositivo_vigencia']]


class DispositivoEdicaoAlteracaoForm(ModelForm):

    class Meta:
        model = Dispositivo
        fields = [
            'dispositivo_atualizador',
            'dispositivo_substituido',
            'dispositivo_subsequente',
        ]
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together':
                _("Já existe um Dispositivo com características idênticas."),
            }
        }

    def __init__(self, *args, **kwargs):

        layout = []

        self.dispositivo_substituido = forms.ModelChoiceField(
            label=Dispositivo._meta.get_field(
                'dispositivo_substituido').verbose_name,
            required=False,
            queryset=Dispositivo.objects.all())
        self.dispositivo_subsequente = forms.ModelChoiceField(
            label=Dispositivo._meta.get_field(
                'dispositivo_subsequente').verbose_name,
            required=False,
            queryset=Dispositivo.objects.all())
        self.dispositivo_atualizador = forms.ModelChoiceField(
            label=Dispositivo._meta.get_field(
                'dispositivo_atualizador').verbose_name,
            required=False,
            queryset=Dispositivo.objects.all())

        substituido = Field(
            'dispositivo_substituido',
            data_sapl_ta='DispositivoSearch',
            data_field='dispositivo_substituido',
            data_type_selection='radio',
            template="compilacao/layout/dispositivo_radio.html")
        subsequente = Field(
            'dispositivo_subsequente',
            data_sapl_ta='DispositivoSearch',
            data_field='dispositivo_subsequente',
            data_type_selection='radio',
            template="compilacao/layout/dispositivo_radio.html")
        alterador = Field(
            'dispositivo_atualizador',
            data_sapl_ta='DispositivoSearch',
            data_field='dispositivo_atualizador',
            data_type_selection='radio',
            data_function='alterador',
            template="compilacao/layout/dispositivo_radio.html")

        layout.append(
            to_row([
                (Fieldset(_('Dispositivo Subsitituido'), substituido), 6),
                (Fieldset(_('Dispositivo Subsequente'), subsequente), 6)]))

        layout.append(
            Fieldset(
                _('Dispositivo Alterador'),
                Div(alterador),
                css_class="col-md-12"))

        inst = kwargs['instance'] if 'instance' in kwargs else None
        if inst and inst.tipo_dispositivo.dispositivo_de_articulacao:
            if 'texto_atualizador' in\
                    DispositivoEdicaoAlteracaoForm.Meta.fields:
                DispositivoEdicaoAlteracaoForm.Meta.fields.remove(
                    'texto_atualizador')
                DispositivoEdicaoAlteracaoForm.Meta.fields.remove(
                    'visibilidade')
        else:
            if 'texto_atualizador' not in\
                    DispositivoEdicaoAlteracaoForm.Meta.fields:
                DispositivoEdicaoAlteracaoForm.Meta.fields.append(
                    'texto_atualizador')
                DispositivoEdicaoAlteracaoForm.Meta.fields.append(
                    'visibilidade')

            self.texto_atualizador = forms.CharField(required=False,
                                                     label='',
                                                     widget=forms.Textarea())
            self.visibilidade = forms.ChoiceField(
                label=Dispositivo._meta.get_field(
                    'visibilidade').verbose_name,
                choices=utils.YES_NO_CHOICES,
                widget=forms.RadioSelect())

            layout.append(
                Fieldset(Dispositivo._meta.get_field(
                    'texto_atualizador').verbose_name,
                    to_row([(InlineRadios('visibilidade'), 12)]),
                    to_row([('texto_atualizador', 12)]),
                    css_class="col-md-12"))

        fields = DispositivoEdicaoAlteracaoForm.Meta.fields
        if fields:
            self.base_fields.clear()
            for f in fields:
                if hasattr(self, f):
                    self.base_fields.update({f: getattr(self, f)})

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(
            *layout,
            label_cancel=_('Ir para o Editor Sequencial'))

        super(DispositivoEdicaoAlteracaoForm, self).__init__(*args, **kwargs)

        self.fields['dispositivo_substituido'].choices = []
        self.fields['dispositivo_subsequente'].choices = []
        self.fields['dispositivo_atualizador'].choices = []
        if inst.dispositivo_substituido:
            self.fields['dispositivo_substituido'].choices = [
                (inst.dispositivo_substituido.pk,
                 inst.dispositivo_substituido)]

        if inst.dispositivo_subsequente:
            self.fields['dispositivo_subsequente'].choices = [
                (inst.dispositivo_subsequente.pk,
                 inst.dispositivo_subsequente)]

        if inst.dispositivo_atualizador:
            self.fields['dispositivo_atualizador'].choices = [
                (inst.dispositivo_atualizador.pk,
                 inst.dispositivo_atualizador)]

    def clean(self):
        """os cleans individuais do framework não puderam ser usados devido
            a última validação compor dois valores
        """
        data = self.cleaned_data

        dst = data['dispositivo_substituido']
        dsq = data['dispositivo_subsequente']
        da = data['dispositivo_atualizador']

        if dst == self.instance:
            raise ValidationError(_('Não é permitido selecionar o próprio '
                                    'Dispositivo como seu substituto.'))
        if dst and dst.ta != self.instance.ta:
            raise ValidationError(_('Não é permitido selecionar um '
                                    'Dispositivo de outro Texto Articulado.'))
        if dst and dst.tipo_dispositivo != self.instance.tipo_dispositivo:
            raise ValidationError(_('Não é permitido selecionar um '
                                    'Dispositivo de outro Tipo.'))

        if dsq == self.instance:
            raise ValidationError(_('Não é permitido selecionar o próprio '
                                    'Dispositivo como seu subsequente.'))
        if dsq and dsq.ta != self.instance.ta:
            raise ValidationError(_('Não é permitido selecionar um '
                                    'Dispositivo de outro Texto Articulado.'))
        if dsq and dsq.tipo_dispositivo != self.instance.tipo_dispositivo:
            raise ValidationError(_('Não é permitido selecionar um '
                                    'Dispositivo de outro Tipo.'))

        if da and not (da.tipo_dispositivo.dispositivo_de_alteracao and
                       da.tipo_dispositivo.dispositivo_de_articulacao):
            raise ValidationError(_('O Dispositivo de Atualização selecionado '
                                    'não é um Bloco de Alteração.'))
        if not da and dst:
            raise ValidationError(_('Não é permitido substituir um '
                                    'Dispositivo sem haver um '
                                    'Dispositivo Alterador.'))

    def save(self):
        data = self.cleaned_data

        od = Dispositivo.objects.get(pk=self.instance.pk)

        nd = self.instance
        ndst = data['dispositivo_substituido']
        ndsq = data['dispositivo_subsequente']
        nda = data['dispositivo_atualizador']

        if ndst != od.dispositivo_substituido:
            if od.dispositivo_substituido:
                odst = od.dispositivo_substituido

                odst.dispositivo_subsequente = None
                odst.fim_vigencia = None
                odst.fim_eficacia = None
                odst.save()

            if ndst:
                if ndst.dispositivo_subsequente:
                    ndst.dispositivo_subsequente.dispositivo_substituido = None
                    ndst.dispositivo_subsequente.save()

                ndst.dispositivo_subsequente = nd
                ndst.fim_vigencia = nd.inicio_vigencia - timedelta(days=1)
                ndst.fim_eficacia = nd.inicio_eficacia - timedelta(days=1)
                ndst.save()

        if ndsq != od.dispositivo_subsequente:
            if od.dispositivo_subsequente:
                odsq = od.dispositivo_subsequente

                odsq.dispositivo_substituido = None
                odsq.save()

            if ndsq:
                if ndsq.dispositivo_substituido:
                    ndsq.dispositivo_substituido.dispositivo_subsequente = None
                    ndsq.dispositivo_substituido.fim_vigencia = None
                    ndsq.dispositivo_substituido.fim_eficacia = None
                    ndsq.dispositivo_substituido.save()

                ndsq.dispositivo_substituido = nd
                ndsq.save()

        nd.ta_publicado = nda.ta if nda else None

        super(DispositivoEdicaoAlteracaoForm, self).save()

        if nd.dispositivo_subsequente:
            nd.fim_vigencia = nd.dispositivo_subsequente.inicio_vigencia - \
                timedelta(days=1)
            nd.fim_eficacia = nd.dispositivo_subsequente.inicio_eficacia - \
                timedelta(days=1)
        nd.save()


class TextNotificacoesForm(Form):

    type_notificacoes = forms.ChoiceField(
        label=_('Níveis de Notificações'),
        choices=[('default', _('Dispositivos sem Notificações!')),
                 ('success', _('Informações!')),
                 ('info', _('Boas Práticas!')),
                 ('warning', _('Alertas!')),
                 ('danger', _('Erros!'))],
        required=False)

    def __init__(self, *args, **kwargs):

        field_type_notificacoes = to_row([(Field(
            'type_notificacoes',
            template="compilacao/layout/bootstrap_btn_checkbox.html"), 10),
            (Submit('submit-form', _('Filtrar'),
                    css_class='btn btn-primary pull-right'), 2)])

        self.helper = FormHelper()
        self.helper.layout = Layout(field_type_notificacoes)

        super(TextNotificacoesForm, self).__init__(*args, **kwargs)
