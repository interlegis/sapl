from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Fieldset, Layout
from django import forms
from django.forms import ModelForm

import sapl
from sapl.layout import form_actions

from .models import CasaLegislativa

ESTADOS = {"": "",
           "AC": "ACRE",
           "AL": "ALAGOAS",
           "AM": "AMAZONAS",
           "AP": "AMAPÁ",
           "BA": "BAHIA",
           "CE": "CEARÁ",
           "DF": "DISTRITO FEDERAL",
           "ES": "ESPíRITO SANTO",
           "GO": "GOIÁS",
           "MA": "MARANHÃO",
           "MG": "MINAS GERAIS",
           "MS": "MATO GROSSO DO SUL",
           "MT": "MATO GROSSO",
           "PA": "PARÁ",
           "PB": "PARAÍBA",
           "PE": "PERNAMBUCO",
           "PI": "PIAUÍ",
           "PR": "PARANÁ",
           "RJ": "RIO DE JANEIRO",
           "RN": "RIO GRANDE DO NORTE",
           "RO": "RONDÔNIA",
           "RR": "RORAIMA",
           "RS": "RIO GRANDE DO SUL",
           "SC": "SANTA CATARINA",
           "SE": "SERGIPE",
           "SP": "SÃO PAULO",
           "TO": "TOCANTINS"}


class CasaLegislativaTabelaAuxForm(ModelForm):

    uf = forms.ChoiceField(required=True,
                           label='UF',
                           choices=[(uf, uf) for uf in ESTADOS.keys()],
                           widget=forms.Select(
                               attrs={'class': 'selector'}))

    informacao_geral = forms.CharField(widget=forms.Textarea,
                                       label='Informação Geral',
                                       required=False)

    telefone = forms.CharField(label='Telefone',
                               required=False,
                               widget=forms.TextInput(
                                   attrs={'class': 'telefone'}))

    logotipo = forms.ImageField(label='Logotipo',
                                required=False,
                                widget=forms.FileInput
                                )

    cep = forms.CharField(label='Cep',
                          required=True,
                          widget=forms.TextInput(
                              attrs={'class': 'cep'}))

    fax = forms.CharField(label='Fax',
                          required=False,
                          widget=forms.TextInput(
                              attrs={'class': 'telefone'}))

    class Meta:

        model = CasaLegislativa
        fields = ['codigo',
                  'nome',
                  'sigla',
                  'endereco',
                  'cep',
                  'municipio',
                  'uf',
                  'telefone',
                  'fax',
                  'logotipo',
                  'endereco_web',
                  'email',
                  'informacao_geral']

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('codigo', 2),
             ('nome', 5),
             ('sigla', 5)])

        row2 = sapl.layout.to_row(
            [('endereco', 8),
             ('cep', 4)])

        row3 = sapl.layout.to_row(
            [('municipio', 10),
             ('uf', 2)])

        row4 = sapl.layout.to_row(
            [('telefone', 6),
             ('fax', 6)])

        row5 = sapl.layout.to_row(
            [('logotipo', 12)])

        row6 = sapl.layout.to_row(
            [('endereco_web', 12)])

        row7 = sapl.layout.to_row(
            [('email', 12)])

        row8 = sapl.layout.to_row(
            [('informacao_geral', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Dados Básicos',
                row1,
                row2,
                row3,
                row4,
                row5,
                HTML("""{% if form.logotipo.value %}
                        <img class="img-responsive" width="225" height="300"
                             src="{{ MEDIA_URL }}{{ form.logotipo.value }}">
                             <br /><br />
                        <input type="submit"
                               name="remover"
                               id="remover"
                               class="button primary"
                               value="Remover Logo"/>
                         {% endif %}""", ),
                row6,
                row7,
                row8,
                form_actions()
            )
        )
        super(CasaLegislativaTabelaAuxForm, self).__init__(*args, **kwargs)
