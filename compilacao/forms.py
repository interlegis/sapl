from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Field,\
    Div, Column, Row, Hidden, Button
from django import forms
from django.core.urlresolvers import reverse
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _

from compilacao.models import Nota, TipoNota, Dispositivo
import sapl


class UpLoadImportFileForm(forms.Form):
    import_file = forms.FileField(
        required=True,
        label=_('Arquivo formato ODF para Importanção'))


def get_tipos_nota():
    return [(t.id, t.sigla + ' - ' + t.nome) for t in TipoNota.objects.all()]


class NotaForm(ModelForm):
    NPRIV = 1
    NSTRL = 2
    NINST = 3
    NPUBL = 4

    PUBLICIDADE_CHOICES = (
        # Only the owner of the note has visibility.
        (NPRIV, _('Nota Privada')),
        # All of the same group have visibility.
        (NSTRL, _('Nota Setorial')),
        # All authenticated users have visibility.
        (NINST, _('Nota Institucional')),
        # All users have visibility.
        (NPUBL, _('Nota Pública')),
    )
    error_messages = {
        'required': _('Este campo é obrigatório'),
        'invalid': _('URL inválida.')
    }
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
        label='Publicidade',
        choices=PUBLICIDADE_CHOICES,
        widget=forms.Select(attrs={'class': 'selector'}))

    tipo = forms.ModelChoiceField(
        required=False,
        label='Tipo da Nota',
        queryset=TipoNota.objects.all(),
        empty_label=None)

    publicacao = forms.DateField(
        label=u'Publicação',
        input_formats=['%d/%m/%Y'],
        required=True,
        widget=forms.DateInput(
            format='%d/%m/%Y'),
        error_messages=error_messages
    )
    efetividade = forms.DateField(
        label=u'Efetividade',
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

        row1 = sapl.layout.to_row([
            ('tipo', 4),
        ])
        row1.append(
            Column(
                Field(
                    'titulo',
                    placeholder=_('Título da Nota (opcional)')
                ),
                css_class='columns large-8'))

        row3 = sapl.layout.to_row([
            ('publicidade', 3),
            ('publicacao', 3),
            ('efetividade', 3),
            (Button('submit', 'Salvar',
                    css_class='button primary'), 3)
        ])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            row1,
            Field('texto', placeholder=_('Adicionar Nota')),
            Field('url_externa', placeholder=_('URL Externa (opcional)')),
            row3
        )

        kwargs.pop('norma_id')
        dispositivo_id = kwargs.pop('dispositivo_id')
        if 'pk' in kwargs:
            pk = kwargs.pop('pk')
        else:
            pk = ''

        super(NotaForm, self).__init__(*args, **kwargs)

        self.fields['dispositivo'].initial = dispositivo_id
        if pk:
            self.fields['pk'].initial = pk
