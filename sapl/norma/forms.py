import logging

from crispy_forms.layout import (Button, Fieldset, HTML, Layout)
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q
from django.forms import ModelChoiceField, ModelForm, widgets
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import django_filters

from sapl.base.models import Autor, TipoAutor
from sapl.crispy_layout_mixin import form_actions, SaplFormHelper, to_row
from sapl.materia.forms import choice_anos_com_materias
from sapl.materia.models import (MateriaLegislativa,
                                 TipoMateriaLegislativa, Orgao)
from sapl.parlamentares.models import Partido
from sapl.utils import (autor_label, autor_modal, ANO_CHOICES,  choice_anos_com_normas,
                        FileFieldCheckMixin, FilterOverridesMetaMixin,
                        NormaPesquisaOrderingFilter, RangeWidgetOverride,
                        validar_arquivo)

from .models import (AnexoNormaJuridica, AssuntoNorma, AutoriaNorma,
                     NormaJuridica, NormaRelacionada, TipoNormaJuridica)


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


class AssuntoNormaFilterSet(django_filters.FilterSet):
    assunto = django_filters.CharFilter(label=_("Assunto"),
                                        method='multifield_filter')

    class Meta:
        model = AssuntoNorma
        fields = ["assunto"]

    def multifield_filter(self, queryset, name, value):
        return queryset.filter(Q(assunto__icontains=value) | Q(descricao__icontains=value))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row0 = to_row([("assunto", 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = "GET"
        self.form.helper.layout = Layout(
            Fieldset(
                _("Pesquisa de Assunto de Norma Jurídica"),
                row0, form_actions(label="Pesquisar"))
        )


class NormaFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=False,
                                      label='Ano',
                                      choices=choice_anos_com_normas)

    ementa = django_filters.CharFilter(
        method='filter_ementa',
        label=_('Pesquisar expressões na ementa da norma'))

    indexacao = django_filters.CharFilter(lookup_expr='icontains',
                                          label=_('Indexação'))

    assuntos = django_filters.ModelChoiceFilter(
        queryset=AssuntoNorma.objects.all())

    autorianorma__autor = django_filters.CharFilter(widget=forms.HiddenInput())
    autorianorma__primeiro_autor = django_filters.BooleanFilter(
        required=False,
        label=_('Primeiro Autor'))
    autorianorma__autor__parlamentar_set__filiacao__partido = django_filters.ModelChoiceFilter(
        queryset=Partido.objects.all(),
        label=_('Normas por Partido'))

    o = NormaPesquisaOrderingFilter(help_text='')

    class Meta(FilterOverridesMetaMixin):
        model = NormaJuridica
        fields = ['orgao', 'tipo', 'numero', 'ano', 'data',
                  'data_vigencia', 'data_publicacao', 'ementa', 'assuntos',
                  'autorianorma__autor', 'autorianorma__primeiro_autor', 'autorianorma__autor__tipo']

    def __init__(self, *args, **kwargs):
        super(NormaFilterSet, self).__init__(*args, **kwargs)
        self.filters['autorianorma__autor__tipo'].label = _('Tipo de Autor')

        row1 = to_row([('tipo', 4), ('numero', 4), ('ano', 4)])
        row2 = to_row([('data', 6), ('data_publicacao', 6)])
        row3 = to_row([('ementa', 6), ('assuntos', 6)])
        row4 = to_row([('data_vigencia', 6), ('orgao', 6), ])
        row5 = to_row([('o', 6), ('indexacao', 6)])
        row6 = to_row([
            ('autorianorma__autor', 0),
            (Button('pesquisar',
                    'Pesquisar Autor',
                    css_class='btn btn-primary btn-sm'), 2),
            (Button('limpar',
                    'Limpar Autor',
                    css_class='btn btn-primary btn-sm'), 2),
            ('autorianorma__primeiro_autor', 2),
            ('autorianorma__autor__tipo', 3),
            ('autorianorma__autor__parlamentar_set__filiacao__partido', 3)
        ])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Norma'),
                     row1, row2, row3, row4, row5,
            Fieldset(_('Pesquisa Avançada'),
                     row6,
                     HTML(autor_label),
                     HTML(autor_modal)),
                     form_actions(label='Pesquisar'))
        )

    def filter_ementa(self, queryset, name, value):
        texto = value.split()
        q = Q()
        for t in texto:
            q &= Q(ementa__icontains=t)

        return queryset.filter(q)

    def filter_autoria(self, queryset, name, value):
        return queryset.filter(**{
            name: value,
        })


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
                  'orgao',
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
                  'user',
                  'ip',
                  'ultima_edicao']

        widgets = {'assuntos': widgets.CheckboxSelectMultiple,
                   'user': forms.HiddenInput(),
                   'ip': forms.HiddenInput(),
                   'ultima_edicao': forms.HiddenInput()}

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
            params = {
                'ano': cleaned_data['ano'],
                'numero': cleaned_data['numero'],
                'tipo': cleaned_data['tipo'],
            }
            params['orgao'] = cleaned_data['orgao']
            norma = NormaJuridica.objects.filter(**params).exists()
            if norma:
                self.logger.warning("Já existe uma norma de mesmo Tipo ({}), Ano ({}) "
                                    "e Número ({}) no sistema."
                                    .format(cleaned_data['tipo'], cleaned_data['ano'], cleaned_data['numero']))
                raise ValidationError("Já existe uma norma de mesmo Tipo, Ano, Órgão "
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

        if texto_integral:
            validar_arquivo(texto_integral, "Texto Integral")

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

    legislatura_anterior = forms.BooleanField(label=_('Legislatura Anterior'),
                                              required=False)

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super(AutoriaNormaForm, self).__init__(*args, **kwargs)

        row1 = to_row([('tipo_autor', 4),
                       ('autor', 4),
                       ('primeiro_autor', 4)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Autoria'),
                     row1, 'data_relativa',
                     form_actions(label='Salvar'),
                     to_row([('legislatura_anterior', 12)])))

        if not self.instance:
            self.fields['autor'].choices = []


    class Meta:
        model = AutoriaNorma
        fields = ['tipo_autor', 'autor',
                  'primeiro_autor', 'data_relativa',
                  'legislatura_anterior']

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

    logger = logging.getLogger(__name__)

    anexo_arquivo = forms.FileField(
        required=True,
        label="Arquivo Anexo"
    )

    class Meta:
        model = AnexoNormaJuridica
        fields = ['norma', 'anexo_arquivo', 'assunto_anexo']
        widgets = {
            'norma': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super(AnexoNormaJuridicaForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        anexo_arquivo = self.cleaned_data.get('anexo_arquivo', False)

        if anexo_arquivo:
            validar_arquivo(anexo_arquivo, "Arquivo Anexo")

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

    orgao = forms.ModelChoiceField(
        label='Órgão',
        required=False,
        queryset=Orgao.objects.all(),
        empty_label='----------',
    )
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
        fields = ['orgao', 'tipo', 'numero', 'ano', 'ementa', 'tipo_vinculo']

    def __init__(self, *args, **kwargs):
        super(NormaRelacionadaForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(NormaRelacionadaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data
        cleaned_data = self.cleaned_data

        try:
            self.logger.debug("Tentando obter objeto NormaJuridica com numero={}, ano={}, tipo={}, orgao={}.".format(
                cleaned_data['numero'], cleaned_data['ano'], cleaned_data['tipo'], cleaned_data['orgao']))
            norma_relacionada = NormaJuridica.objects.get(
                numero=cleaned_data['numero'],
                ano=cleaned_data['ano'],
                tipo=cleaned_data['tipo'],
                orgao=cleaned_data['orgao'])
        except ObjectDoesNotExist:
            self.logger.info("NormaJuridica com numero={}, ano={}, tipo={}, orgao={} não existe.".format(
                cleaned_data['numero'], cleaned_data['ano'], cleaned_data['tipo'], cleaned_data['orgao']))
            msg = _('A norma a ser relacionada não existe.')
            raise ValidationError(msg)
        else:
            self.logger.info("NormaJuridica com numero={}, ano={}, tipo={} , orgao={} obtida com sucesso.".format(
                cleaned_data['numero'], cleaned_data['ano'], cleaned_data['tipo'], cleaned_data['orgao']))
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
                self.logger.error("Data Final ({}) menor que a Data Inicial ({}).".format(
                    data_final, data_inicial))
                raise ValidationError(
                    _('A Data Final não pode ser menor que a Data Inicial'))

        return cleaned_data
