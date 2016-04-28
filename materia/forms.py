import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Column, Fieldset, Layout, Submit
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Max
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
import sapl
from crispy_layout_mixin import form_actions
from norma.models import LegislacaoCitada, TipoNormaJuridica
from sapl.settings import MAX_DOC_UPLOAD_SIZE
from sapl.utils import RANGE_ANOS

from .models import (AcompanhamentoMateria, Anexada, Autor, Autoria,
                     DespachoInicial, DocumentoAcessorio, MateriaLegislativa,
                     Numeracao, Proposicao, Relatoria, TipoMateriaLegislativa,
                     Tramitacao)

ANO_CHOICES = [('', '---------')] + RANGE_ANOS


def em_tramitacao():
    return [('', 'Tanto Faz'),
            (True, 'Sim'),
            (False, 'Não')]


class ProposicaoForm(ModelForm):

    tipo_materia = forms.ModelChoiceField(
        label=_('Matéria Vinculada'),
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero_materia = forms.CharField(
        label='Número', required=False)

    ano_materia = forms.CharField(
        label='Ano', required=False)

    def clean_texto_original(self):
        texto_original = self.cleaned_data.get('texto_original', False)
        if texto_original:
            if texto_original.size > MAX_DOC_UPLOAD_SIZE:
                raise ValidationError("Arquivo muito grande. ( > 5mb )")
            return texto_original

    class Meta:
        model = Proposicao
        fields = ['tipo', 'data_envio', 'descricao', 'texto_original']

    def __init__(self, excluir=False, *args, **kwargs):
        more = []
        if excluir:
            more = [Submit('Excluir', 'Excluir')]

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 8), ('data_envio', 4)])
        row2 = crispy_layout_mixin.to_row(
            [('descricao', 12)])
        row3 = crispy_layout_mixin.to_row(
            [('tipo_materia', 4), ('numero_materia', 4), ('ano_materia', 4)])
        row4 = crispy_layout_mixin.to_row(
            [('texto_original', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Incluir Proposição'),
                     row1, row2, row3, row4,
                     HTML("""
                    <div class="img-responsive" width="225" height="300"
                      src="{{ MEDIA_URL }}{{ form.texto_original.value }}">
                      <br /><br />
                    <input type="submit"
                               name="remover-texto"
                               id="remover-texto"
                               class="btn btn-warning"
                               value="Remover Texto"/>
                    <p></p>
                           """, ),
                     form_actions(more=more))
        )
        super(ProposicaoForm, self).__init__(
            *args, **kwargs)


class AcompanhamentoMateriaForm(ModelForm):

    class Meta:
        model = AcompanhamentoMateria
        fields = ['email']

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row([('email', 10)])

        row1.append(
            Column(form_actions(save_label='Cadastrar'), css_class='col-md-2')
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Acompanhamento de Matéria por e-mail'), row1
            )
        )
        super(AcompanhamentoMateriaForm, self).__init__(*args, **kwargs)


class DocumentoAcessorioForm(ModelForm):
    autor = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = DocumentoAcessorio
        fields = ['tipo',
                  'nome',
                  'data',
                  'autor',
                  'ementa']
        widgets = {
            'data': forms.DateInput(attrs={'class': 'dateinput'})
        }

    def clean_autor(self):
        autor_field = self.cleaned_data['autor']
        try:
            int(autor_field)
        except ValueError:
            return autor_field
        else:
            if autor_field:
                return str(Autor.objects.get(id=autor_field))

    def __init__(self, excluir=False, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 4), ('nome', 4), ('data', 4)])

        row2 = crispy_layout_mixin.to_row(
            [('autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'Limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])

        row3 = crispy_layout_mixin.to_row(
            [('ementa', 12)])

        more = []
        if excluir:
            more = [Submit('Excluir', 'Excluir')]

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Incluir Documento Acessório'),
                row1,
                HTML(sapl.utils.autor_label),
                HTML(sapl.utils.autor_modal),
                row2, row3,
                form_actions(more=more)
            )
        )
        super(DocumentoAcessorioForm, self).__init__(*args, **kwargs)


class RelatoriaForm(ModelForm):

    class Meta:
        model = Relatoria
        fields = ['data_designacao_relator',
                  'comissao',
                  'parlamentar',
                  'data_destituicao_relator',
                  'tipo_fim_relatoria'
                  ]
        widgets = {
            'data_designacao_relator': forms.DateInput(attrs={
                'class': 'dateinput'}),
            'data_destituicao_relator': forms.DateInput(attrs={
                                                        'class': 'dateinput'}),
        }


class TramitacaoForm(ModelForm):
    urgente = forms.ChoiceField(required=False,
                                label='Tramitando',
                                choices=[(True, 'Sim'), (False, 'Não')],
                                widget=forms.Select(
                                    attrs={'class': 'selector'}))

    class Meta:
        model = Tramitacao
        fields = ['data_tramitacao',
                  'unidade_tramitacao_local',
                  'status',
                  'turno',
                  'urgente',
                  'unidade_tramitacao_destino',
                  'data_encaminhamento',
                  'data_fim_prazo',
                  'texto']

    def __init__(self, excluir=False, *args, **kwargs):
        row1 = crispy_layout_mixin.to_row(
            [('data_tramitacao', 6), ('unidade_tramitacao_local', 6)])

        row2 = crispy_layout_mixin.to_row(
            [('status', 5), ('turno', 5), ('urgente', 2)])

        row3 = crispy_layout_mixin.to_row(
            [('unidade_tramitacao_destino', 12)])

        row4 = crispy_layout_mixin.to_row(
            [('data_encaminhamento', 6), ('data_fim_prazo', 6)])

        row5 = crispy_layout_mixin.to_row(
            [('texto', 12)])

        more = []
        if excluir:
            more = [Submit('Excluir', 'Excluir')]
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Incluir Tramitação'),
                     row1, row2, row3, row4, row5,
                     ),
            form_actions(more=more)
        )
        super(TramitacaoForm, self).__init__(
            *args, **kwargs)


class LegislacaoCitadaForm(ModelForm):

    tipo = forms.ModelChoiceField(
        label=_('Tipo Norma'),
        required=True,
        queryset=TipoNormaJuridica.objects.all(),
        empty_label='Selecione',
    )

    numero = forms.CharField(label='Número', required=True)

    ano = forms.CharField(label='Ano', required=True)

    class Meta:
        model = LegislacaoCitada
        fields = ['tipo',
                  'numero',
                  'ano',
                  'disposicoes',
                  'parte',
                  'livro',
                  'titulo',
                  'capitulo',
                  'secao',
                  'subsecao',
                  'artigo',
                  'paragrafo',
                  'inciso',
                  'alinea',
                  'item']


class NumeracaoForm(ModelForm):

    class Meta:
        model = Numeracao
        fields = ['tipo_materia',
                  'numero_materia',
                  'ano_materia',
                  'data_materia']

    def clean(self):
        if self.errors:
            return self.errors

        try:
            MateriaLegislativa.objects.get(
                numero=self.cleaned_data['numero_materia'],
                ano=self.cleaned_data['ano_materia'],
                tipo=self.cleaned_data['tipo_materia'])
        except ObjectDoesNotExist:
            msg = _('A matéria a ser inclusa não existe no cadastro'
                    ' de matérias legislativas.')
            raise ValidationError(msg)

        if Numeracao.objects.filter(
            materia=self.instance.materia,
            tipo_materia=self.cleaned_data['tipo_materia'],
            ano_materia=self.cleaned_data['ano_materia'],
            numero_materia=self.cleaned_data['numero_materia']
        ).exists():
            msg = _('Essa numeração já foi cadastrada.')
            raise ValidationError(msg)

        return self.cleaned_data


class AnexadaForm(ModelForm):

    tipo = forms.ModelChoiceField(
        label='Tipo',
        required=True,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero = forms.CharField(label='Número', required=True)

    ano = forms.CharField(label='Ano', required=True)

    def clean(self):
        if self.errors:
            return self.errors

        cleaned_data = self.cleaned_data

        try:
            materia_anexada = MateriaLegislativa.objects.get(
                numero=cleaned_data['numero'],
                ano=cleaned_data['ano'],
                tipo=cleaned_data['tipo'])
        except ObjectDoesNotExist:
            msg = _('A matéria a ser anexada não existe no cadastro'
                    ' de matérias legislativas.')
            raise ValidationError(msg)
        else:
            cleaned_data['materia_anexada'] = materia_anexada

        return cleaned_data

    def save(self, commit=False):
        anexada = super(AnexadaForm, self).save(commit)
        anexada.materia_anexada = self.cleaned_data['materia_anexada']
        anexada.save()
        return anexada

    class Meta:
        model = Anexada
        fields = ['tipo', 'numero', 'ano', 'data_anexacao', 'data_desanexacao']


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


class MateriaLegislativaFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    ano = django_filters.ChoiceFilter(required=False,
                                      label=u'Ano da Matéria',
                                      choices=ANO_CHOICES)

    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    ementa = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = MateriaLegislativa
        fields = ['numero',
                  'numero_protocolo',
                  'ano',
                  'tipo',
                  'data_apresentacao',
                  'data_publicacao',
                  'autoria__autor__tipo',
                  'autoria__partido',
                  'relatoria__parlamentar_id',
                  'local_origem_externa',
                  'tramitacao__unidade_tramitacao_destino',
                  'tramitacao__status',
                  'em_tramitacao',
                  ]

        order_by = (
            ('', 'Selecione'),
            ('dataC', 'Data, Tipo, Ano, Numero - Ordem Crescente'),
            ('dataD', 'Data, Tipo, Ano, Numero - Ordem Decrescente'),
            ('tipoC', 'Tipo, Ano, Numero, Data - Ordem Crescente'),
            ('tipoD', 'Tipo, Ano, Numero, Data - Ordem Decrescente')
        )

    order_by_mapping = {
        '': [],
        'dataC': ['data_apresentacao', 'tipo__sigla', 'ano', 'numero'],
        'dataD': ['-data_apresentacao', '-tipo__sigla', '-ano', '-numero'],
        'tipoC': ['tipo__sigla', 'ano', 'numero', 'data_apresentacao'],
        'tipoD': ['-tipo__sigla', '-ano', '-numero', '-data_apresentacao'],
    }

    def get_order_by(self, order_value):
        if order_value in self.order_by_mapping:
            return self.order_by_mapping[order_value]
        else:
            return super(MateriaLegislativaFilterSet,
                         self).get_order_by(order_value)

    def __init__(self, *args, **kwargs):
        super(MateriaLegislativaFilterSet, self).__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters['autoria__autor__tipo'].label = 'Tipo de Autor'
        self.filters['autoria__partido'].label = 'Partido do Autor'
        self.filters['relatoria__parlamentar_id'].label = 'Relatoria'

        row1 = crispy_layout_mixin.to_row(
            [('tipo', 12)])
        row2 = crispy_layout_mixin.to_row(
            [('numero', 4),
             ('ano', 4),
             ('numero_protocolo', 4)])
        row3 = crispy_layout_mixin.to_row(
            [('data_apresentacao', 6),
             ('data_publicacao', 6)])
        row4 = crispy_layout_mixin.to_row(
            [('autoria__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])
        row5 = crispy_layout_mixin.to_row(
            [('autoria__autor__tipo', 6),
             ('autoria__partido', 6)])
        row6 = crispy_layout_mixin.to_row(
            [('relatoria__parlamentar_id', 6),
             ('local_origem_externa', 6)])
        row7 = crispy_layout_mixin.to_row(
            [('tramitacao__unidade_tramitacao_destino', 6),
             ('tramitacao__status', 6)])
        row8 = crispy_layout_mixin.to_row(
            [('em_tramitacao', 6),
             ('o', 6)])
        row9 = crispy_layout_mixin.to_row(
            [('ementa', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa Básica'),
                     row1, row2, row3,
                     HTML(sapl.utils.autor_label),
                     HTML(sapl.utils.autor_modal),
                     row4, row5, row6, row7, row8, row9,
                     form_actions(save_label='Pesquisar'))
        )


def pega_ultima_tramitacao():
    ultimas_tramitacoes = Tramitacao.objects.values(
        'materia_id').annotate(data_encaminhamento=Max(
            'data_encaminhamento'),
        id=Max('id')).values_list('id')

    lista = [item for sublist in ultimas_tramitacoes for item in sublist]

    return lista


def filtra_tramitacao_status(status):
    lista = pega_ultima_tramitacao()
    return Tramitacao.objects.filter(
      id__in=lista,
      status=status).distinct().values_list('materia_id', flat=True)


def filtra_tramitacao_destino(destino):
    lista = pega_ultima_tramitacao()
    return Tramitacao.objects.filter(
      id__in=lista,
      unidade_tramitacao_destino=destino).distinct().values_list(
      'materia_id', flat=True)


def filtra_tramitacao_destino_and_status(status, destino):
    lista = pega_ultima_tramitacao()
    return Tramitacao.objects.filter(
      id__in=lista,
      status=status,
      unidade_tramitacao_destino=destino).distinct().values_list(
      'materia_id', flat=True)


class DespachoInicialForm(ModelForm):

    class Meta:
        model = DespachoInicial
        fields = ['comissao']

    def clean(self):
        if self.errors:
            return self.errors

        if DespachoInicial.objects.filter(
            materia=self.instance.materia,
            comissao=self.cleaned_data['comissao'],
        ).exists():
            msg = _('Esse Despacho já foi cadastrado.')
            raise ValidationError(msg)

        return self.cleaned_data


class AutoriaForm(ModelForm):

    class Meta:
        model = Autoria
        fields = ['autor', 'partido', 'primeiro_autor']

    def clean(self):
        if self.errors:
            return self.errors

        if Autoria.objects.filter(
            materia=self.instance.materia,
            autor=self.cleaned_data['autor'],
        ).exists():
            msg = _('Esse Autor já foi cadastrado.')
            raise ValidationError(msg)

        return self.cleaned_data
