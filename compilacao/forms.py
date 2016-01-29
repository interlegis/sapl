from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import (HTML, Column, Div, Fieldset,
                                            Layout, Row)
from crispy_forms_foundation.layout.buttons import Button
from crispy_forms_foundation.layout.fields import Field
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from compilacao.models import (PARTICIPACAO_SOCIAL_CHOICES, Dispositivo, Nota,
                               Publicacao, TextoArticulado, TipoNota,
                               TipoPublicacao, TipoTextoArticulado, TipoVide,
                               VeiculoPublicacao, Vide)
from sapl.layout import SaplFormLayout, to_column, to_row
from sapl.utils import YES_NO_CHOICES


class UpLoadImportFileForm(forms.Form):
    import_file = forms.FileField(
        required=True,
        label=_('Arquivo formato ODF para Importanção'))

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
                     row1, css_class="large-12"))
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
            Fieldset(_('Identificação Básica'), row1, css_class="large-12"),
            Fieldset(
                TextoArticulado._meta.get_field('ementa').verbose_name,
                Column('ementa'), css_class="large-12"),
            Fieldset(
                TextoArticulado._meta.get_field('observacao').verbose_name,
                Column('observacao'), css_class="large-12"),

        )

        super(TaForm, self).__init__(*args, **kwargs)


class NotaForm(ModelForm):
    NPRIV = 1
    NINST = 2
    NPUBL = 3

    PUBLICIDADE_CHOICES = (
        # Only the owner of the note has visibility.
        (NPRIV, _('Nota Privada')),
        # All authenticated users have visibility.
        (NINST, _('Nota Institucional')),
        # All users have visibility.
        (NPUBL, _('Nota Pública')),
    )
    titulo = forms.CharField(label='&nbsp;', required=False)
    texto = forms.CharField(
        label='',
        widget=forms.Textarea,
        error_messages=error_messages)
    url_externa = forms.URLField(
        label='',
        required=False,
        error_messages=error_messages)
    publicidade = forms.ChoiceField(
        required=True,
        label=_('Publicidade'),
        choices=PUBLICIDADE_CHOICES,
        widget=forms.Select(attrs={'class': 'selector'}))

    tipo = forms.ModelChoiceField(
        required=False,
        label=_('Tipo da Nota'),
        queryset=TipoNota.objects.all(),
        empty_label=None)

    publicacao = forms.DateField(
        label=_('Publicação'),
        input_formats=['%d/%m/%Y'],
        required=True,
        widget=forms.DateInput(
            format='%d/%m/%Y'),
        error_messages=error_messages
    )
    efetividade = forms.DateField(
        label=_('Efetividade'),
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
                css_class='columns large-8'))

        row3 = to_row([
            ('publicidade', 3),
            ('publicacao', 3),
            ('efetividade', 3),
            (Button('submit', _('Salvar'),
                    css_class='btn btn-primary'), 3)
        ])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(HTML(_('Notas')), css_class='title_form'),
            row1,
            Field('texto', placeholder=_('Adicionar Nota')),
            Field('url_externa', placeholder=_('URL Externa (opcional)')),
            row3
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

        self.helper = FormHelper()
        self.helper.layout = Layout(

            Div(HTML(_('Vides')), css_class='title_form'),

            Row(
                to_column((
                    Div(
                        Div(to_column((Field(
                            'tipo',
                            placeholder=_('Selecione um Tipo de Vide')), 12))),
                        Div(to_column((
                            Field(
                                'texto',
                                placeholder=_(
                                    'Texto Adicional ao Vide')), 12))),
                        Div(to_column((
                            Button(
                                'submit',
                                'Salvar',
                                css_class='btn btn-primary'), 12)))
                    ), 4)),
                to_column((
                    Div(
                        Div(to_column(('tipo_ta', 6))),
                        Div(to_column(('num_ta', 3)),
                            to_column(('ano_ta', 3))),
                        Div(to_column(
                            (Field(
                                'busca_dispositivo',
                                placeholder=_('Digite palavras, letras, '
                                              'números ou algo'
                                              ' que estejam '
                                              'no rótulo ou no texto.')), 10)),
                            to_column((
                                Button(
                                    'buscar',
                                    'Buscar',
                                    css_class='btn btn-primary btn-busca'), 2))

                            ),
                        to_column(
                            (Div(css_class='container-busca'), 12))
                    ), 8)
                )
            )
        )

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
                     row1, row2, row3, css_class="large-12"))

        super(PublicacaoForm, self).__init__(*args, **kwargs)
        pass
