import sapl

from django.views.generic.base import TemplateView
from .models import CasaLegislativa
from django.forms import ModelForm
from django import forms
from django.views.generic.edit import FormMixin
from vanilla import GenericView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (HTML, ButtonHolder, Column, Fieldset, Layout,
                                 Submit)
from django.core.exceptions import ObjectDoesNotExist

from django.core.urlresolvers import reverse

class HelpView(TemplateView):
    # XXX treat non existing template as a 404!!!!

    def get_template_names(self):
        print(self.kwargs['topic'])
        return ['ajuda/%s.html' % self.kwargs['topic']]


ESTADOS = ["AC",
           "AL",
           "AM",
           "AP",
           "BA",
           "CE",
           "DF",
           "ES",
           "GO",
           "MA",
           "MG",
           "MS",
           "MT",
           "PA",
           "PB",
           "PE",
           "PI",
           "PR",
           "RJ",
           "RN",
           "RO",
           "RR",
           "RS",
           "SC",
           "SE",
           "SP",
           "TO"]


class CasaLegislativaTabelaAuxForm(ModelForm):

    uf = forms.ChoiceField(required=False,
                           label='UF',
                           choices=[(a,a) for a in ESTADOS],
                           widget=forms.Select(
                           attrs={'class': 'selector'}))

    informacao_geral = forms.CharField(widget=forms.Textarea, 
                                       label='informacao_geral', 
                                       required=True)

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
                row6,
                row7,
                row8,
                ButtonHolder(
                    Submit('submit', 'Salvar',
                           css_class='button primary')
                )
            )
        )
        super(CasaLegislativaTabelaAuxForm, self).__init__(*args, **kwargs)

class CasaLegislativaTableAuxView(FormMixin, GenericView):

    template_name = "base/casa_leg_table_aux.html"

    def get(self, request, *args, **kwargs):
        try:
            casa = CasaLegislativa.objects.first()
        except ObjectDoesNotExist:
            form = CasaLegislativaTabelaAuxForm()
        else:
            form = CasaLegislativaTabelaAuxForm(instance=casa)

        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = CasaLegislativaTabelaAuxForm(request.POST or request.FILES)

        if form.is_valid():
            try:
                casa = CasaLegislativa.objects.first()
            except ObjectDoesNotExist:
                casa_save = form.save(commit=False)
            else:
                casa_save = CasaLegislativaTabelaAuxForm(request.POST, instance = casa)

            if 'logotipo' in request.FILES:
                casa_save.logotipo = request.FILES['logotipo']

            casa_save.save()

            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form})

    def get_success_url(self):
        return reverse('casa_legislativa')
