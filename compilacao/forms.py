from crispy_forms.bootstrap import FieldWithButtons, FormActions, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (HTML, Button, Column, Div, Field, Fieldset,
                                 Layout, Row)
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from compilacao.models import (NOTAS_PUBLICIDADE_CHOICES,
                               PARTICIPACAO_SOCIAL_CHOICES, Dispositivo, Nota,
                               Publicacao, TextoArticulado, TipoNota,
                               TipoPublicacao, TipoTextoArticulado, TipoVide,
                               VeiculoPublicacao, Vide)
from crispy_layout_mixin import SaplFormLayout, to_column, to_row
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
        queryset=Dispositivo.objects.all(),
        widget=forms.HiddenInput())

    tipo_ta = forms.ModelChoiceField(
        label=_('Tipo do Texto Articulado'),
        queryset=TipoTextoArticulado.objects.all(),
        required=False)

    tipo_model = forms.ChoiceField(
        choices=[],
        label=_('Tipos de...'), required=False)

    num_ta = forms.IntegerField(
        label=_('Núm Texto Articulado'), required=False)
    ano_ta = forms.IntegerField(
        label=_('Ano Texto Articulado'), required=False)

    texto = forms.CharField(
        label='',
        widget=forms.Textarea,
        required=False)
    tipo = forms.ModelChoiceField(
        label=TipoVide._meta.verbose_name,
        queryset=TipoVide.objects.all(),
        required=True,
        error_messages=error_messages)

    busca_dispositivo = forms.CharField(
        label=_('Buscar Dispositivo a Referenciar'),
        required=False)
    pk = forms.IntegerField(widget=forms.HiddenInput(),
                            required=False)

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

        fields_form = Div(
            Row(to_column((Field(
                'tipo',
                placeholder=_('Selecione um Tipo de Vide')), 12))),
            Row(to_column((Field(
                'texto',
                placeholder=_('Texto Adicional ao Vide')), 12))),
            Row(to_column((buttons, 12))))

        fields_search = Div(
            Row(
                to_column(('tipo_ta', 6)),
                to_column(('tipo_model', 6))),
            Row(
                to_column(('num_ta', 6)),
                to_column(('ano_ta', 6))),
            Row(to_column((FieldWithButtons(
                Field(
                    'busca_dispositivo',
                    placeholder=_('Digite palavras, letras, '
                                  'números ou algo'
                                  ' que estejam '
                                  'no rótulo ou no texto.')),
                StrictButton("Buscar", css_class='btn-busca')), 12))),
            Row(to_column(
                (Div(css_class='container-busca'), 12)))
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(HTML(_('Vides')), css_class='panel-heading'),
                Div(
                    to_column((
                        fields_form, 4)),
                    to_column((
                        fields_search, 8)), css_class="panel-body"
                ),
                css_class="panel panel-primary"
            )
        )

        if 'choice_model_type_foreignkey_in_extenal_views' in kwargs:
            ch = kwargs.pop('choice_model_type_foreignkey_in_extenal_views')
            if 'data' in kwargs:
                choice = ch(kwargs['data']['tipo_ta'])
                self.base_fields['tipo_model'].choices = choice

        super(VideForm, self).__init__(*args, **kwargs)


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

    texto = forms.CharField(
        widget=forms.Textarea,
        required=False)

    dispositivo1 = DispositivoIntegerField(
        label=('1&ordf; %s' % _('Variação')),
        field_name='dispositivo1')
    dispositivo2 = DispositivoIntegerField(
        label=('2&ordf;'),
        field_name='dispositivo2')
    dispositivo3 = DispositivoIntegerField(
        label=('3&ordf;'),
        field_name='dispositivo3')
    dispositivo4 = DispositivoIntegerField(
        label=('4&ordf;'),
        field_name='dispositivo4')
    dispositivo5 = DispositivoIntegerField(
        label=('5&ordf;'),
        field_name='dispositivo5')

    rotulo = forms.CharField(label=_('Rótulo Resultante'))

    class Meta:
        model = Dispositivo
        fields = (
            'dispositivo0',
            'dispositivo1',
            'dispositivo2',
            'dispositivo3',
            'dispositivo4',
            'dispositivo5',
            'rotulo',
            'texto')

        widgets = {
            'dispositivo0': forms.NumberInput(
                attrs={'title': _('Valor 0(zero) é permitido apenas '
                                  'para Dispositivos com tipos variáveis.'),
                       'onchange': 'atualizaRotulo()'})}

    def __init__(self, *args, **kwargs):

        layout = []

        rotulo_fieldset = to_row([
            ('dispositivo0', 3),
            ('dispositivo1', 2),
            ('dispositivo2', 1),
            ('dispositivo3', 1),
            ('dispositivo4', 1),
            ('dispositivo5', 1),
            ('rotulo', 3)
        ])

        layout.append(
            Fieldset(
                _('Montagem do Rótulo'),
                rotulo_fieldset,
                css_class="col-md-12"))

        # Campo Texto
        row_texto = to_row([('texto', 12)])
        css_class_texto = "col-md-12"
        if 'instance' in kwargs and\
                kwargs['instance'].tipo_dispositivo.dispositivo_de_articulacao:
            css_class_texto = "col-md-12 hidden"
        layout.append(
            Fieldset(
                Dispositivo._meta.get_field('texto').verbose_name,
                row_texto,
                css_class=css_class_texto))

        self.helper = FormHelper()
        if layout:
            self.helper.layout = SaplFormLayout(*layout)
        else:
            self.helper.layout = SaplFormLayout()

        super(DispositivoEdicaoBasicaForm, self).__init__(*args, **kwargs)
