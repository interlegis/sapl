
import logging

from sapl.crispy_layout_mixin import SaplFormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q
from django.forms import ModelForm, widgets, ModelChoiceField
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import django_filters

from sapl.base.models import Autor, TipoAutor
from sapl.crispy_layout_mixin import form_actions, to_row
from sapl.materia.forms import choice_anos_com_materias
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.settings import MAX_DOC_UPLOAD_SIZE
from sapl.utils import NormaPesquisaOrderingFilter, RangeWidgetOverride, \
    choice_anos_com_normas, FilterOverridesMetaMixin, FileFieldCheckMixin, ANO_CHOICES

from .models import (AnexoNormaJuridica, AssuntoNorma, NormaJuridica, NormaRelacionada,
                     TipoNormaJuridica, AutoriaNorma)


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

    ano = django_filters.ChoiceFilter(required=False,
                                      label='Ano',
                                      choices=choice_anos_com_normas)

    ementa = django_filters.CharFilter(
        method='filter_ementa',
        label=_('Pesquisar expressões na ementa da norma'))

    apelido = django_filters.CharFilter(lookup_expr='icontains',
                                          label=_('Apelido'))

    indexacao = django_filters.CharFilter(lookup_expr='icontains',
                                          label=_('Indexação'))

    assuntos = django_filters.ModelChoiceFilter(
        queryset=AssuntoNorma.objects.all())

    o = NormaPesquisaOrderingFilter(help_text='')

    class Meta(FilterOverridesMetaMixin):
        model = NormaJuridica
        fields = ['tipo', 'numero', 'ano', 'data', 'data_vigencia',
                  'data_publicacao', 'ementa', 'assuntos', 'apelido']

    def __init__(self, *args, **kwargs):
        super(NormaFilterSet, self).__init__(*args, **kwargs)

        row1 = to_row([('tipo', 4), ('numero', 4), ('ano', 4)])
        row2 = to_row([('ementa', 6), ('assuntos', 6)])
        row3 = to_row([('data', 6), ('data_publicacao', 6)])
        row4 = to_row([('data_vigencia', 12)])
        row5 = to_row([('o', 4), ('indexacao', 4), ('apelido', 4)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Norma'),
                     row1, row2, row3, row4, row5,
                     form_actions(label='Pesquisar'))
        )

    def filter_ementa(self, queryset, name, value):
        texto = value.split()
        q = Q()
        for t in texto:
            q &= Q(ementa__icontains=t)

        return queryset.filter(q)


class NormaJuridicaForm(FileFieldCheckMixin, ModelForm):

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

    logger = logging.getLogger(__name__)

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
                  'data_vigencia',
                  'veiculo_publicacao',
                  'pagina_inicio_publicacao',
                  'pagina_fim_publicacao',
                  'ementa',
                  'indexacao',
                  'observacao',
                  'texto_integral',
                  'assuntos',
                  'norma_de_destaque',
                  'apelido',
                  'user', 
                  'ip']
                  
        widgets = {'assuntos': widgets.CheckboxSelectMultiple,
                    'user': forms.HiddenInput(),
                    'ip': forms.HiddenInput()}

    def clean(self):

        cleaned_data = super(NormaJuridicaForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        import re
        has_digits = re.sub('[^0-9]', '', cleaned_data['numero'])
        if not has_digits:
            self.logger.error("Número de norma ({}) não pode conter somente letras.".format(
                cleaned_data['numero']))
            raise ValidationError(
                'Número de norma não pode conter somente letras')

        if self.instance.numero != cleaned_data['numero']:
            norma = NormaJuridica.objects.filter(ano=cleaned_data['ano'],
                                                 numero=cleaned_data['numero'],
                                                 tipo=cleaned_data['tipo']).exists()
            if norma:
                self.logger.error("Já existe uma norma de mesmo Tipo ({}), Ano ({}) "
                                  "e Número ({}) no sistema."
                                  .format(cleaned_data['tipo'], cleaned_data['ano'], cleaned_data['numero']))
                raise ValidationError("Já existe uma norma de mesmo Tipo, Ano "
                                      "e Número no sistema")
        if (cleaned_data['tipo_materia'] and
            cleaned_data['numero_materia'] and
                cleaned_data['ano_materia']):
            try:
                self.logger.debug("Tentando obter objeto MateriaLegislativa com tipo={}, numero={}, ano={}."
                                  .format(cleaned_data['tipo_materia'], cleaned_data['numero_materia'], cleaned_data['ano_materia']))
                materia = MateriaLegislativa.objects.get(
                    tipo_id=cleaned_data['tipo_materia'],
                    numero=cleaned_data['numero_materia'],
                    ano=cleaned_data['ano_materia'])

            except ObjectDoesNotExist:
                self.logger.error("Matéria Legislativa %s/%s (%s) é inexistente." % (
                    self.cleaned_data['numero_materia'],
                    self.cleaned_data['ano_materia'],
                    cleaned_data['tipo_materia'].descricao))
                raise forms.ValidationError(
                    _("Matéria Legislativa %s/%s (%s) é inexistente." % (
                        self.cleaned_data['numero_materia'],
                        self.cleaned_data['ano_materia'],
                        cleaned_data['tipo_materia'].descricao)))
            else:
                self.logger.info("MateriaLegislativa com tipo={}, numero={}, ano={} obtida com sucesso."
                                 .format(cleaned_data['tipo_materia'], cleaned_data['numero_materia'], cleaned_data['ano_materia']))
                cleaned_data['materia'] = materia

        else:
            cleaned_data['materia'] = None

        return cleaned_data

    def clean_texto_integral(self):
        super(NormaJuridicaForm, self).clean()

        texto_integral = self.cleaned_data.get('texto_integral', False)

        if texto_integral and texto_integral.size > MAX_DOC_UPLOAD_SIZE:
            raise ValidationError("O arquivo Texto Integral deve ser menor que {0:.1f} mb, o tamanho atual desse arquivo é {1:.1f} mb" \
                .format((MAX_DOC_UPLOAD_SIZE/1024)/1024, (texto_integral.size/1024)/1024))

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

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super(AutoriaNormaForm, self).__init__(*args, **kwargs)

        row1 = to_row([('tipo_autor', 4),
                       ('autor', 4),
                       ('primeiro_autor', 4)])

        self.helper = SaplFormHelper()
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
            self.logger.error(
                "Autor ({}) já foi cadastrado.".format(cd['autor']))
            raise ValidationError(_('Esse Autor já foi cadastrado.'))

        return cd


class AnexoNormaJuridicaForm(FileFieldCheckMixin, ModelForm):
    class Meta:
        model = AnexoNormaJuridica
        fields = ['norma', 'anexo_arquivo', 'assunto_anexo']
        widgets = {
            'norma': forms.HiddenInput(),
        }

    logger = logging.getLogger(__name__)

    def clean(self):
        cleaned_data = super(AnexoNormaJuridicaForm, self).clean()
        
        if not self.is_valid():
            return cleaned_data
        
        anexo_arquivo = self.cleaned_data.get('anexo_arquivo', False)

        if anexo_arquivo and anexo_arquivo.size > MAX_DOC_UPLOAD_SIZE:
            raise ValidationError("O Arquivo Anexo deve ser menor que {0:.1f} mb, o tamanho atual desse arquivo é {1:.1f} mb" \
                .format((MAX_DOC_UPLOAD_SIZE/1024)/1024, (anexo_arquivo.size/1024)/1024))

        return cleaned_data

    def save(self, commit=False):
        anexo = self.instance
        anexo.ano = self.cleaned_data['norma'].ano
        anexo.norma = self.cleaned_data['norma']
        anexo.assunto_anexo = self.cleaned_data['assunto_anexo']
        anexo.anexo_arquivo = self.cleaned_data['anexo_arquivo']
        anexo = super(AnexoNormaJuridicaForm, self).save(commit=True)
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

    logger = logging.getLogger(__name__)

    class Meta:
        model = NormaRelacionada
        fields = ['tipo', 'numero', 'ano', 'ementa', 'tipo_vinculo']

    def __init__(self, *args, **kwargs):
        super(NormaRelacionadaForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(NormaRelacionadaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data
        cleaned_data = self.cleaned_data

        try:
            self.logger.debug("Tentando obter objeto NormaJuridica com numero={}, ano={}, tipo={}.".format(
                cleaned_data['numero'], cleaned_data['ano'], cleaned_data['tipo']))
            norma_relacionada = NormaJuridica.objects.get(
                numero=cleaned_data['numero'],
                ano=cleaned_data['ano'],
                tipo=cleaned_data['tipo'])
        except ObjectDoesNotExist:
            self.logger.info("NormaJuridica com numero={}, ano={}, tipo={} não existe.".format(
                cleaned_data['numero'], cleaned_data['ano'], cleaned_data['tipo']))
            msg = _('A norma a ser relacionada não existe.')
            raise ValidationError(msg)
        else:
            self.logger.info("NormaJuridica com numero={}, ano={}, tipo={} obtida com sucesso.".format(
                cleaned_data['numero'], cleaned_data['ano'], cleaned_data['tipo']))
            cleaned_data['norma_relacionada'] = norma_relacionada

        return cleaned_data

    def save(self, commit=False):
        relacionada = super(NormaRelacionadaForm, self).save(commit)
        relacionada.norma_relacionada = self.cleaned_data['norma_relacionada']
        if relacionada.tipo_vinculo.revoga_integralmente:
            relacionada.norma_relacionada.data_vigencia = relacionada.norma_principal.data
        relacionada.norma_relacionada.save()
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

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row1 = to_row(
            [('tipo_norma', 6),
             ('data_inicial', 3),
             ('data_final', 3)])

        row2 = to_row(
            [('titulo', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Índice de Normas',
                row1, row2,
                form_actions(label='Pesquisar')
            )
        )

    def clean(self):
        super().clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data
        data_inicial = cleaned_data['data_inicial']
        data_final = cleaned_data['data_final']

        if data_inicial or data_final:
            if not(data_inicial and data_final):
                self.logger.error("Caso pesquise por data, os campos de Data Inicial e "
                                  "Data Final devem ser preenchidos obrigatoriamente")
                raise ValidationError(_('Caso pesquise por data, os campos de Data Inicial e '
                                        'Data Final devem ser preenchidos obrigatoriamente'))
            elif data_inicial > data_final:
                self.logger.error("Data Final ({}) menor que a Data Inicial ({}).".format(data_final, data_inicial))
                raise ValidationError(_('A Data Final não pode ser menor que a Data Inicial'))

        return cleaned_data
