
import django_filters
import logging
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.forms import ModelForm, widgets, ModelChoiceField
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import Autor, TipoAutor
from sapl.crispy_layout_mixin import form_actions, to_row
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.settings import MAX_DOC_UPLOAD_SIZE
from sapl.utils import NormaPesquisaOrderingFilter, RANGE_ANOS, RangeWidgetOverride

from .models import (AnexoNormaJuridica, AssuntoNorma, NormaJuridica, NormaRelacionada,
                     TipoNormaJuridica, AutoriaNorma)


def ANO_CHOICES():
    return [('', '---------')] + RANGE_ANOS


def get_esferas():
    return [('E', 'Estadual'),
            ('F', 'Federal'),
            ('M', 'Municipal')]


YES_NO_CHOICES = [('', '---------'),
                  (True, _('Sim')),
                  (False, _('Não'))]

ORDENACAO_CHOICES = [('', '---------'),
                     ('tipo,ano,numero', _('Tipo/Ano/Número')),
                     ('data,tipo,ano,numero', _('Data/Tipo/Ano/Número'))]


class NormaFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    ano = django_filters.ChoiceFilter(required=False,
                                      label='Ano',
                                      choices=ANO_CHOICES)

    ementa = django_filters.CharFilter(lookup_expr='icontains')

    indexacao = django_filters.CharFilter(lookup_expr='icontains',
                                          label=_('Indexação'))

    assuntos = django_filters.ModelChoiceFilter(
        queryset=AssuntoNorma.objects.all())

    o = NormaPesquisaOrderingFilter()

    class Meta:
        model = NormaJuridica
        fields = ['tipo', 'numero', 'ano', 'data',
                  'data_publicacao', 'ementa', 'assuntos']

    def __init__(self, *args, **kwargs):
        super(NormaFilterSet, self).__init__(*args, **kwargs)

        row1 = to_row([('tipo', 4), ('numero', 4), ('ano', 4)])
        row2 = to_row([('data', 6), ('data_publicacao', 6)])
        row3 = to_row([('ementa', 6), ('assuntos', 6)])
        row4 = to_row([('o',6), ('indexacao', 6)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Norma'),
                     row1, row2, row3, row4,
                     form_actions(label='Pesquisar'))
        )


class NormaJuridicaForm(ModelForm):

    # Campos de MateriaLegislativa
    tipo_materia = forms.ModelChoiceField(
        label='Matéria',
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
        widget=forms.Select(attrs={'autocomplete': 'off'})
    )
    numero_materia = forms.CharField(
        label='Número Matéria',
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )
    ano_materia = forms.ChoiceField(
        label='Ano Matéria',
        required=False,
        choices=ANO_CHOICES,
        widget=forms.Select(attrs={'autocomplete': 'off'})
    )

    class Meta:
        model = NormaJuridica
        fields = ['tipo',
                  'numero',
                  'ano',
                  'data',
                  'esfera_federacao',
                  'complemento',
                  'tipo_materia',
                  'numero_materia',
                  'ano_materia',
                  'data_publicacao',
                  'veiculo_publicacao',
                  'pagina_inicio_publicacao',
                  'pagina_fim_publicacao',
                  'ementa',
                  'indexacao',
                  'observacao',
                  'texto_integral',
                  'assuntos']
        widgets = {'assuntos': widgets.CheckboxSelectMultiple}


    def clean(self):
        logger = logging.getLogger(__name__)
        cleaned_data = super(NormaJuridicaForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        import re
        has_digits = re.sub('[^0-9]', '', cleaned_data['numero'])
        if not has_digits:
            raise ValidationError('Número de norma não pode conter somente letras')

        if self.instance.numero != cleaned_data['numero']:
            norma = NormaJuridica.objects.filter(ano=cleaned_data['ano'],
                                                 numero=cleaned_data['numero'],
                                                 tipo=cleaned_data['tipo']).exists()
            if norma:
                raise ValidationError("Já existe uma norma de mesmo Tipo, Ano "
                                      "e Número no sistema")
        if (cleaned_data['tipo_materia'] and
                cleaned_data['numero_materia'] and
                cleaned_data['ano_materia']):
            try:
                logger.info("- Tentando obter objeto MateriaLegislativa.")
                materia = MateriaLegislativa.objects.get(
                    tipo_id=cleaned_data['tipo_materia'],
                    numero=cleaned_data['numero_materia'],
                    ano=cleaned_data['ano_materia'])

            except ObjectDoesNotExist:
                logger.error("- Matéria Legislativa %s/%s (%s) é inexistente." % (
                        self.cleaned_data['numero_materia'],
                        self.cleaned_data['ano_materia'],
                        cleaned_data['tipo_materia'].descricao))
                raise forms.ValidationError(
                    _("Matéria Legislativa %s/%s (%s) é inexistente." % (
                        self.cleaned_data['numero_materia'],
                        self.cleaned_data['ano_materia'],
                        cleaned_data['tipo_materia'].descricao)))
            else:
                cleaned_data['materia'] = materia

        else:
            cleaned_data['materia'] = None

        ano = cleaned_data['ano']
        data = cleaned_data['data']

        if data.year != ano:
            logger.error("O ano da norma é diferente "
                        "do ano no campo data")
            raise ValidationError("O ano da norma não pode ser "
                                  "diferente do ano no campo data")
        return cleaned_data

    def clean_texto_integral(self):
        logger = logging.getLogger(__name__)
        texto_integral = self.cleaned_data.get('texto_integral', False)
        if texto_integral and texto_integral.size > MAX_DOC_UPLOAD_SIZE:
            max_size = str(MAX_DOC_UPLOAD_SIZE / (1024 * 1024))
            logger.error("- Arquivo muito grande. ( > {0}MB )".format(max_size))
            raise ValidationError(
                  "Arquivo muito grande. ( > {0}MB )".format(max_size))
        return texto_integral

    def save(self, commit=False):
        norma = self.instance
        norma.timestamp = timezone.now()
        norma.materia = self.cleaned_data['materia']
        norma = super(NormaJuridicaForm, self).save(commit=True)

        return norma


class AutoriaNormaForm(ModelForm):

    tipo_autor = ModelChoiceField(label=_('Tipo Autor'),
                                  required=False,
                                  queryset=TipoAutor.objects.all(),
                                  empty_label=_('Selecione'),)

    data_relativa = forms.DateField(
        widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(AutoriaNormaForm, self).__init__(*args, **kwargs)

        row1 = to_row([('tipo_autor', 4),
                       ('autor', 4),
                       ('primeiro_autor', 4)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Autoria'),
                     row1, 'data_relativa', form_actions(label='Salvar')))

        if not kwargs['instance']:
            self.fields['autor'].choices = []

    class Meta:
        model = AutoriaNorma
        fields = ['tipo_autor', 'autor', 'primeiro_autor', 'data_relativa']

    def clean(self):
        cd = super(AutoriaNormaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        autorias = AutoriaNorma.objects.filter(
            norma=self.instance.norma, autor=cd['autor'])
        pk = self.instance.pk

        if ((not pk and autorias.exists()) or
                (pk and autorias.exclude(pk=pk).exists())):
            raise ValidationError(_('Esse Autor já foi cadastrado.'))

        return cd

class AnexoNormaJuridicaForm(ModelForm):
    class Meta:
        model = AnexoNormaJuridica
        fields = ['norma', 'anexo_arquivo', 'assunto_anexo']
        widgets = {
            'norma': forms.HiddenInput(),
        }

    def clean(self):
        logger = logging.getLogger(__name__)
        cleaned_data = super(AnexoNormaJuridicaForm, self).clean()
        if not self.is_valid():
            return cleaned_data
        anexo_arquivo = self.cleaned_data.get('anexo_arquivo', False)
        if anexo_arquivo and anexo_arquivo.size > MAX_DOC_UPLOAD_SIZE:
            max_size = str(MAX_DOC_UPLOAD_SIZE / (1024 * 1024))
            logger.error("- Arquivo muito grande. ( > {0}MB )".format(max_size))
            raise ValidationError(
                 "Arquivo muito grande. ( > {0}MB )".format(max_size))
        return cleaned_data

    def save(self, commit=False):
        anexo = self.instance
        anexo.ano = self.cleaned_data['norma'].ano
        anexo = super(AnexoNormaJuridicaForm, self).save(commit=True)
        anexo.norma = self.cleaned_data['norma']
        anexo.assunto_anexo = self.cleaned_data['assunto_anexo']
        anexo.anexo_arquivo = self.cleaned_data['anexo_arquivo']
        anexo.save()
        return anexo



class NormaRelacionadaForm(ModelForm):

    tipo = forms.ModelChoiceField(
        label='Tipo',
        required=True,
        queryset=TipoNormaJuridica.objects.all(),
        empty_label='----------',
    )
    numero = forms.CharField(label='Número', required=True)
    ano = forms.CharField(label='Ano', required=True)
    ementa = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'disabled': 'disabled'}))

    class Meta:
        model = NormaRelacionada
        fields = ['tipo', 'numero', 'ano', 'ementa', 'tipo_vinculo']

    def __init__(self, *args, **kwargs):
        super(NormaRelacionadaForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(NormaRelacionadaForm, self).clean()
        logger = logging.getLogger(__name__)

        if not self.is_valid():
            return self.cleaned_data
        cleaned_data = self.cleaned_data

        try:
            logger.info("- Tentando obter objeto NormaJuridica. ")
            norma_relacionada = NormaJuridica.objects.get(
                numero=cleaned_data['numero'],
                ano=cleaned_data['ano'],
                tipo=cleaned_data['tipo'])
        except ObjectDoesNotExist:
            logger.error("- A norma a ser relacionada não existe.")
            msg = _('A norma a ser relacionada não existe.')
            raise ValidationError(msg)
        else:
            cleaned_data['norma_relacionada'] = norma_relacionada

        return cleaned_data

    def save(self, commit=False):
        relacionada = super(NormaRelacionadaForm, self).save(commit)
        relacionada.norma_relacionada = self.cleaned_data['norma_relacionada']
        relacionada.save()
        return relacionada


class NormaPesquisaSimplesForm(forms.Form):
    tipo_norma = forms.ModelChoiceField(
        label=TipoNormaJuridica._meta.verbose_name,
        queryset=TipoNormaJuridica.objects.all(),
        required=False,
        empty_label='Selecione')

    data_inicial = forms.DateField(
        label='Data Inicial',
        required=False,
        widget=forms.DateInput(format='%d/%m/%Y')
    )

    data_final = forms.DateField(
        label='Data Final',
        required=False,
        widget=forms.DateInput(format='%d/%m/%Y')
    )

    titulo = forms.CharField(
        label='Título do Relatório',
        required=False,
        max_length=150)

    def __init__(self, *args, **kwargs):
        super(NormaPesquisaSimplesForm, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('tipo_norma', 6),
             ('data_inicial', 3),
             ('data_final', 3)])

        row2 = to_row(
            [('titulo', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                ('Índice de Normas'),
                row1, row2,
                form_actions(label='Pesquisar')
            )
        )

    def clean(self):
        super(NormaPesquisaSimplesForm, self).clean()
        logger = logging.getLogger(__name__)

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        data_inicial = cleaned_data['data_inicial']
        data_final = cleaned_data['data_final']

        if (data_inicial and data_final and
                data_inicial > data_final):
            logger.error("- Data Final menor que a Data Inicial")
            raise ValidationError(_(
                'A Data Final não pode ser menor que a Data Inicial'))
        else:
            condicao1 = data_inicial and not data_final
            condicao2 = not data_inicial and data_final
            if condicao1 or condicao2:
                logger.error("- Caso pesquise por data, os campos de Data Inicial e "
                            "Data Final devem ser preenchidos obrigatoriamente")
                raise ValidationError(_('Caso pesquise por data, os campos de Data Inicial e ' +
                                        'Data Final devem ser preenchidos obrigatoriamente'))

        return cleaned_data
