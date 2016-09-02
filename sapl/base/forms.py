import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Fieldset, Layout
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from sapl.crispy_layout_mixin import form_actions, to_row
from sapl.materia.models import MateriaLegislativa
from sapl.settings import MAX_IMAGE_UPLOAD_SIZE
from sapl.utils import (RANGE_ANOS, ImageThumbnailFileInput, autor_label,
                        autor_modal)

from .models import CasaLegislativa


class RangeWidgetOverride(forms.MultiWidget):

    def __init__(self, attrs=None):
        widgets = (forms.DateInput(format='%d/%m/%Y',
                                   attrs={'class': 'dateinput',
                                          'placeholder': 'Inicial'}),
                   forms.DateInput(format='%d/%m/%Y',
                                   attrs={'class': 'dateinput',
                                          'placeholder': 'Final'}))
        super(RangeWidgetOverride, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]

    def format_output(self, rendered_widgets):
        return ''.join(rendered_widgets)


class RelatorioHistoricoTramitacaoFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    class Meta:
        model = MateriaLegislativa
        fields = ['tipo', 'tramitacao__unidade_tramitacao_local',
                  'tramitacao__status', 'tramitacao__data_tramitacao']

    def __init__(self, *args, **kwargs):
        super(RelatorioHistoricoTramitacaoFilterSet, self).__init__(
                *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'

        row1 = to_row([('tramitacao__data_tramitacao', 12)])
        row2 = to_row(
            [('tipo', 4),
             ('tramitacao__unidade_tramitacao_local', 4),
             ('tramitacao__status', 4)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Histórico de Tramita'),
                     row1, row2,
                     form_actions(save_label='Pesquisar'))
        )


class RelatorioMateriasTramitacaoilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label=u'Ano da Matéria',
                                      choices=RANGE_ANOS)

    class Meta:
        model = MateriaLegislativa
        fields = ['ano', 'tipo', 'tramitacao__unidade_tramitacao_local',
                  'tramitacao__status']

    def __init__(self, *args, **kwargs):
        super(RelatorioMateriasTramitacaoilterSet, self).__init__(
              *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'

        row1 = to_row([('ano', 12)])
        row2 = to_row([('tipo', 12)])
        row3 = to_row([('tramitacao__unidade_tramitacao_local', 12)])
        row4 = to_row([('tramitacao__status', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria em Tramitação'),
                     row1, row2, row3, row4,
                     form_actions(save_label='Pesquisar'))
        )


class RelatorioMateriasPorAnoAutorTipoFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label=u'Ano da Matéria',
                                      choices=RANGE_ANOS)

    class Meta:
        model = MateriaLegislativa
        fields = ['ano']

    def __init__(self, *args, **kwargs):
        super(RelatorioMateriasPorAnoAutorTipoFilterSet, self).__init__(
            *args, **kwargs)

        row1 = to_row(
            [('ano', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1,
                     form_actions(save_label='Pesquisar'))
        )


class RelatorioMateriasPorAutorFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    class Meta:
        model = MateriaLegislativa
        fields = ['tipo', 'data_apresentacao']

    def __init__(self, *args, **kwargs):
        super(RelatorioMateriasPorAutorFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'

        row1 = to_row(
            [('tipo', 12)])
        row2 = to_row(
            [('data_apresentacao', 12)])
        row3 = to_row(
            [('autoria__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1, row2,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row3,
                     form_actions(save_label='Pesquisar'))
        )


class CasaLegislativaForm(ModelForm):

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

        widgets = {
            'uf': forms.Select(attrs={'class': 'selector'}),
            'cep': forms.TextInput(attrs={'class': 'cep'}),
            'telefone': forms.TextInput(attrs={'class': 'telefone'}),
            'fax': forms.TextInput(attrs={'class': 'telefone'}),
            'logotipo':  ImageThumbnailFileInput,
            'informacao_geral': forms.Textarea(
                attrs={'id': 'texto-rico'})
        }

    def clean_logotipo(self):
        logotipo = self.cleaned_data.get('logotipo', False)
        if logotipo:
            if logotipo.size > MAX_IMAGE_UPLOAD_SIZE:
                raise ValidationError("Imagem muito grande. ( > 2mb )")
        return logotipo


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username", max_length=30,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control', 'name': 'username'}))
    password = forms.CharField(
        label="Password", max_length=30,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control', 'name': 'password'}))
