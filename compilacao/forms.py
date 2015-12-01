from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Column, Div, Field, Layout, Row
from django import forms
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from compilacao.models import Dispositivo, Nota, TipoNota, TipoVide, Vide
from norma.models import TipoNormaJuridica
from sapl.layout import to_column, to_row


class UpLoadImportFileForm(forms.Form):
    import_file = forms.FileField(
        required=True,
        label=_('Arquivo formato ODF para Importanção'))

error_messages = {
    'required': _('Este campo é obrigatório'),
    'invalid': _('URL inválida.')
}


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
            (Button('submit', 'Salvar',
                    css_class='button primary radius'), 3)
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

    tipo_norma = forms.ModelChoiceField(
        queryset=TipoNormaJuridica.objects.all(),
        required=False)
    num_norma = forms.IntegerField(label=_('Núm. da Norma'), required=False)
    ano_norma = forms.IntegerField(label=_('Ano da Norma'), required=False)

    texto = forms.CharField(
        label='',
        widget=forms.Textarea,
        error_messages=error_messages,
        required=False)
    tipo = forms.ModelChoiceField(
        label=_('Tipo do Vide'),
        queryset=TipoVide.objects.all(),
        required=True)

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
                                css_class='button primary radius'), 12)))
                    ), 4)),
                to_column((
                    Div(
                        Div(to_column(('tipo_norma', 6))),
                        Div(to_column(('num_norma', 3)),
                            to_column(('ano_norma', 3))),
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
                                    css_class='button btn-busca radius'), 2))

                            ),
                        to_column(
                            (Div(css_class='container-busca'), 12))
                    ), 8)
                )
            )
        )

        super(VideForm, self).__init__(*args, **kwargs)
