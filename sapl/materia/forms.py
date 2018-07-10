
import os

import django_filters
from crispy_forms.bootstrap import Alert, FormActions, InlineRadios
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (HTML, Button, Column, Div, Field, Fieldset,
                                 Layout, Submit)
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.base import File
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models import Max
from django.forms import ModelChoiceField, ModelForm, widgets
from django.forms.forms import Form
from django.forms.models import ModelMultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput, Select
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

import sapl
from sapl.base.models import AppConfig, Autor, TipoAutor
from sapl.comissoes.models import Comissao
from sapl.compilacao.models import (STATUS_TA_IMMUTABLE_PUBLIC,
                                    STATUS_TA_PRIVATE)
from sapl.crispy_layout_mixin import (SaplFormLayout, form_actions, to_column,
                                      to_row)
from sapl.materia.models import (AssuntoMateria, Autoria, MateriaAssunto,
                                 MateriaLegislativa, Orgao, RegimeTramitacao,
                                 TipoDocumento, TipoProposicao, StatusTramitacao,
                                 UnidadeTramitacao)
from sapl.norma.models import (LegislacaoCitada, NormaJuridica,
                               TipoNormaJuridica)
from sapl.parlamentares.models import Legislatura
from sapl.protocoloadm.models import Protocolo, DocumentoAdministrativo
from sapl.settings import MAX_DOC_UPLOAD_SIZE
from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES,
                        ChoiceWithoutValidationField,
                        MateriaPesquisaOrderingFilter, RangeWidgetOverride,
                        autor_label, autor_modal, gerar_hash_arquivo,
                        models_with_gr_for_model, qs_override_django_filter)

from .models import (AcompanhamentoMateria, Anexada, Autoria, DespachoInicial,
                     DocumentoAcessorio, Numeracao, Proposicao, Relatoria,
                     TipoMateriaLegislativa, Tramitacao, UnidadeTramitacao)


def ANO_CHOICES():
    return [('', '---------')] + RANGE_ANOS


def em_tramitacao():
    return [('', 'Tanto Faz'),
            (1, 'Sim'),
            (0, 'Não')]


class AdicionarVariasAutoriasFilterSet(django_filters.FilterSet):

    class Meta:
        model = Autor
        fields = ['nome']

    def __init__(self, *args, **kwargs):
        super(AdicionarVariasAutoriasFilterSet, self).__init__(*args, **kwargs)

        row1 = to_row([('nome', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Filtrar Autores'),
                     row1, form_actions(label='Filtrar'))
        )


class OrgaoForm(ModelForm):

    class Meta:
        model = Orgao
        fields = ['nome', 'sigla', 'unidade_deliberativa',
                  'endereco', 'telefone']

    @transaction.atomic
    def save(self, commit=True):
        orgao = super(OrgaoForm, self).save(commit)
        content_type = ContentType.objects.get_for_model(Orgao)
        object_id = orgao.pk
        tipo = TipoAutor.objects.get(descricao='Órgão')
        nome = orgao.nome + ' - ' + orgao.sigla
        Autor.objects.create(
            content_type=content_type,
            object_id=object_id,
            tipo=tipo,
            nome=nome
        )
        return orgao


class ReceberProposicaoForm(Form):
    cod_hash = forms.CharField(label='Código do Documento', required=True)

    def __init__(self, *args, **kwargs):
        row1 = to_row([('cod_hash', 12)])
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Incorporar Proposição'), row1,
                form_actions(label='Buscar Proposição')
            )
        )
        super(ReceberProposicaoForm, self).__init__(*args, **kwargs)


class MateriaSimplificadaForm(ModelForm):

    class Meta:
        model = MateriaLegislativa
        fields = ['tipo', 'numero', 'ano', 'data_apresentacao',
                  'numero_protocolo', 'regime_tramitacao',
                  'em_tramitacao', 'ementa', 'tipo_apresentacao',
                  'texto_original']

    def __init__(self, *args, **kwargs):

        row1 = to_row([('tipo', 6), ('numero', 3), ('ano', 3)])
        row2 = to_row([('data_apresentacao', 6), ('numero_protocolo', 6)])
        row3 = to_row([('regime_tramitacao', 6), ('em_tramitacao', 3), ('tipo_apresentacao', 3)])
        row4 = to_row([('ementa', 12)])
        row5 = to_row([('texto_original', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Formulário Simplificado'),
                row1, row2, row3, row4, row5,
                form_actions(label='Salvar')
            )
        )
        super(MateriaSimplificadaForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(MateriaSimplificadaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        data_apresentacao = cleaned_data['data_apresentacao']
        ano = cleaned_data['ano']

        if data_apresentacao.year != ano:
            raise ValidationError("O ano da matéria não pode ser "
                                  "diferente do ano na data de apresentação")

        return cleaned_data


class MateriaLegislativaForm(ModelForm):

    tipo_autor = ModelChoiceField(label=_('Tipo Autor'),
                                  required=False,
                                  queryset=TipoAutor.objects.all(),
                                  empty_label=_('------'), )

    autor = forms.ModelChoiceField(required=False,
                                   empty_label='------',
                                   queryset=Autor.objects.all()
                                   )

    class Meta:
        model = MateriaLegislativa
        exclude = ['texto_articulado', 'autores', 'proposicao',
                   'anexadas', 'data_ultima_atualizacao']

    def __init__(self, *args, **kwargs):
        super(MateriaLegislativaForm, self).__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['tipo_autor'] = forms.CharField(required=False,
                                                        widget=forms.HiddenInput())
            self.fields['autor'] = forms.CharField(required=False,
                                                   widget=forms.HiddenInput())
            self.fields['numero_protocolo'].widget.attrs['readonly'] = True

    def clean(self):
        super(MateriaLegislativaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        data_apresentacao = cleaned_data['data_apresentacao']
        ano = cleaned_data['ano']
        protocolo = cleaned_data['numero_protocolo']
        protocolo_antigo = self.instance.numero_protocolo

        if protocolo:
            if not Protocolo.objects.filter(numero=protocolo,ano=ano).exists():
                raise ValidationError(_('Protocolo %s/%s não'
                                        ' existe' % (protocolo, ano)))

            if protocolo_antigo != protocolo:
                exist_materia = MateriaLegislativa.objects.filter(
                                                    numero_protocolo=protocolo,
                                                    ano=ano).exists()

                exist_doc = DocumentoAdministrativo.objects.filter(
                                                        protocolo_id=protocolo,
                                                        ano=ano).exists()

                if exist_materia or exist_doc:
                    raise ValidationError(_('Protocolo %s/%s já possui'
                                            ' documento vinculado'
                                             % (protocolo, ano)))

                p = Protocolo.objects.get(numero=protocolo,ano=ano)
                if p.tipo_materia != cleaned_data['tipo']:
                    raise ValidationError(_('Tipo do Protocolo deve ser o mesmo do Tipo Matéria'))

        if data_apresentacao.year != ano:
            raise ValidationError(_("O ano da matéria não pode ser "
                                  "diferente do ano na data de apresentação"))

        ano_origem_externa = cleaned_data['ano_origem_externa']
        data_origem_externa = cleaned_data['data_origem_externa']

        if ano_origem_externa and data_origem_externa and \
                ano_origem_externa != data_origem_externa.year:
            raise ValidationError(_("O ano de origem externa da matéria não "
                                  "pode ser diferente do ano na data de "
                                  "origem externa"))

        return cleaned_data

    def save(self, commit=False):
        if not self.instance.pk:
            primeiro_autor = True
        else:
            primeiro_autor = False
            
        materia = super(MateriaLegislativaForm, self).save(commit)
        materia.save()

        if self.cleaned_data['autor']:
            autoria = Autoria()
            autoria.primeiro_autor = primeiro_autor
            autoria.materia = materia
            autoria.autor = self.cleaned_data['autor']
            autoria.save()

        return materia

class UnidadeTramitacaoForm(ModelForm):

    class Meta:
        model = UnidadeTramitacao
        fields = ['comissao', 'orgao', 'parlamentar']

    def clean(self):
        super(UnidadeTramitacaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        for key in list(cleaned_data.keys()):
            if cleaned_data[key] is None:
                del cleaned_data[key]

        if len(cleaned_data) != 1:
            msg = _('Somente um campo deve ser preenchido!')
            raise ValidationError(msg)
        return cleaned_data


class AcompanhamentoMateriaForm(ModelForm):

    class Meta:
        model = AcompanhamentoMateria
        fields = ['email']

    def __init__(self, *args, **kwargs):

        row1 = to_row([('email', 10)])

        row1.append(
            Column(form_actions(label='Cadastrar'), css_class='col-md-2')
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Acompanhamento de Matéria por e-mail'), row1
            )
        )
        super(AcompanhamentoMateriaForm, self).__init__(*args, **kwargs)


class DocumentoAcessorioForm(ModelForm):
    data = forms.DateField(required=True)

    class Meta:
        model = DocumentoAcessorio
        fields = ['tipo', 'nome', 'data', 'autor', 'ementa', 'arquivo']


class RelatoriaForm(ModelForm):

    class Meta:
        model = Relatoria
        fields = ['data_designacao_relator', 'comissao', 'parlamentar',
                  'data_destituicao_relator', 'tipo_fim_relatoria']

        widgets = {'comissao': forms.Select(attrs={'disabled': 'disabled'})}

    def __init__(self, *args, **kwargs):
        super(RelatoriaForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(RelatoriaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        try:
            comissao = Comissao.objects.get(id=self.initial['comissao'])
        except ObjectDoesNotExist:
            msg = _('A localização atual deve ser uma comissão.')
            raise ValidationError(msg)
        else:
            cleaned_data['comissao'] = comissao

        return cleaned_data


class TramitacaoForm(ModelForm):

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

    def __init__(self, *args, **kwargs):
        super(TramitacaoForm, self).__init__(*args, **kwargs)
        self.fields['data_tramitacao'].initial = timezone.now().date()

    def clean(self):
        super(TramitacaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        if 'data_encaminhamento' in cleaned_data:
            data_enc_form = cleaned_data['data_encaminhamento']
        if 'data_fim_prazo' in cleaned_data:
            data_prazo_form = cleaned_data['data_fim_prazo']
        if 'data_tramitacao' in cleaned_data:
            data_tram_form = cleaned_data['data_tramitacao']

        ultima_tramitacao = Tramitacao.objects.filter(
            materia_id=self.instance.materia_id).exclude(
            id=self.instance.id).order_by(
            '-data_tramitacao',
            '-id').first()

        if not self.instance.data_tramitacao:

            if ultima_tramitacao:
                destino = ultima_tramitacao.unidade_tramitacao_destino
                if (destino != self.cleaned_data['unidade_tramitacao_local']):
                    msg = _('A origem da nova tramitação deve ser igual ao '
                            'destino  da última adicionada!')
                    raise ValidationError(msg)

            if cleaned_data['data_tramitacao'] > timezone.now().date():
                msg = _(
                    'A data de tramitação deve ser ' +
                    'menor ou igual a data de hoje!')
                raise ValidationError(msg)

            if (ultima_tramitacao and
                    data_tram_form < ultima_tramitacao.data_tramitacao):
                msg = _('A data da nova tramitação deve ser ' +
                        'maior que a data da última tramitação!')
                raise ValidationError(msg)

        if data_enc_form:
            if data_enc_form < data_tram_form:
                msg = _('A data de encaminhamento deve ser ' +
                        'maior que a data de tramitação!')
                raise ValidationError(msg)

        if data_prazo_form:
            if data_prazo_form < data_tram_form:
                msg = _('A data fim de prazo deve ser ' +
                        'maior que a data de tramitação!')
                raise ValidationError(msg)

        return cleaned_data


class TramitacaoUpdateForm(TramitacaoForm):
    unidade_tramitacao_local = forms.ModelChoiceField(
        queryset=UnidadeTramitacao.objects.all(),
        widget=forms.HiddenInput())

    data_tramitacao = forms.DateField(widget=forms.HiddenInput())

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
                  'texto',
                  ]

        widgets = {
            'data_encaminhamento': forms.DateInput(format='%d/%m/%Y'),
            'data_fim_prazo': forms.DateInput(format='%d/%m/%Y'),
        }

    def clean(self):
        super(TramitacaoUpdateForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        ultima_tramitacao = Tramitacao.objects.filter(
            materia_id=self.instance.materia_id).order_by(
            '-data_tramitacao',
            '-id').first()

        # Se a Tramitação que está sendo editada não for a mais recente,
        # ela não pode ter seu destino alterado.
        if ultima_tramitacao != self.instance:
            if self.cleaned_data['unidade_tramitacao_destino'] != \
                    self.instance.unidade_tramitacao_destino:
                raise ValidationError(
                    'Você não pode mudar a Unidade de Destino desta '
                    'tramitação, pois irá conflitar com a Unidade '
                    'Local da tramitação seguinte')

        self.cleaned_data['data_tramitacao'] = \
            self.instance.data_tramitacao
        self.cleaned_data['unidade_tramitacao_local'] = \
            self.instance.unidade_tramitacao_local

        return self.cleaned_data


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

    def clean(self):
        super(LegislacaoCitadaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        try:
            norma = NormaJuridica.objects.get(
                numero=cleaned_data['numero'],
                ano=cleaned_data['ano'],
                tipo=cleaned_data['tipo'])
        except ObjectDoesNotExist:
            msg = _('A norma a ser inclusa não existe no cadastro'
                    ' de Normas.')
            raise ValidationError(msg)
        else:
            cleaned_data['norma'] = norma

        filtro_base = LegislacaoCitada.objects.filter(
            materia=self.instance.materia,
            norma=self.cleaned_data['norma'],
            disposicoes=self.cleaned_data['disposicoes'],
            parte=self.cleaned_data['parte'],
            livro=self.cleaned_data['livro'],
            titulo=self.cleaned_data['titulo'],
            capitulo=self.cleaned_data['capitulo'],
            secao=self.cleaned_data['secao'],
            subsecao=self.cleaned_data['subsecao'],
            artigo=self.cleaned_data['artigo'],
            paragrafo=self.cleaned_data['paragrafo'],
            inciso=self.cleaned_data['inciso'],
            alinea=self.cleaned_data['alinea'],
            item=self.cleaned_data['item'])

        if not self.instance.id:
            if filtro_base.exists():
                msg = _('Essa Legislação já foi cadastrada.')
                raise ValidationError(msg)
        else:
            if filtro_base.exclude(id=self.instance.id).exists():
                msg = _('Essa Legislação já foi cadastrada.')
                raise ValidationError(msg)
        return cleaned_data

    def save(self, commit=False):
        legislacao = super(LegislacaoCitadaForm, self).save(commit)

        legislacao.norma = self.cleaned_data['norma']
        legislacao.save()
        return legislacao


class NumeracaoForm(ModelForm):

    class Meta:
        model = Numeracao
        fields = ['tipo_materia',
                  'numero_materia',
                  'ano_materia',
                  'data_materia']

    def clean(self):
        super(NumeracaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

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

    def __init__(self, *args, **kwargs):

        return super(AnexadaForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(AnexadaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

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

        materia_principal = self.instance.materia_principal
        if materia_principal == materia_anexada:
            raise ValidationError(_('Matéria não pode ser anexada a si mesma'))

        is_anexada = Anexada.objects.filter(materia_principal=materia_principal,
                                            materia_anexada=materia_anexada
                                            ).exists()
        if is_anexada:
            raise ValidationError(_('Materia já se encontra anexada'))

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


class MateriaLegislativaFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    ano = django_filters.ChoiceFilter(required=False,
                                      label='Ano da Matéria',
                                      choices=ANO_CHOICES)

    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    autoria__primeiro_autor = django_filters.BooleanFilter(
        required=False,
        label='Primeiro Autor',
        widget=forms.HiddenInput())

    ementa = django_filters.CharFilter(lookup_expr='icontains')
    indexacao = django_filters.CharFilter(lookup_expr='icontains')

    em_tramitacao = django_filters.ChoiceFilter(required=False,
                                                label='Em tramitação',
                                                choices=em_tramitacao)

    materiaassunto__assunto = django_filters.ModelChoiceFilter(
        queryset=AssuntoMateria.objects.all(),
        label=_('Assunto da Matéria'))

    numeracao__numero_materia = django_filters.NumberFilter(
        required=False,
        label=_('Número do Processo'))

    o = MateriaPesquisaOrderingFilter()

    class Meta:
        model = MateriaLegislativa
        fields = ['numero',
                  'numero_protocolo',
                  'numeracao__numero_materia',
                  'ano',
                  'tipo',
                  'data_apresentacao',
                  'data_publicacao',
                  'autoria__autor__tipo',
                  'autoria__primeiro_autor',
                  # FIXME 'autoria__autor__partido',
                  'relatoria__parlamentar_id',
                  'local_origem_externa',
                  'tramitacao__unidade_tramitacao_destino',
                  'tramitacao__status',
                  'materiaassunto__assunto',
                  'em_tramitacao',
                  ]

    def __init__(self, *args, **kwargs):
        super(MateriaLegislativaFilterSet, self).__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters['autoria__autor__tipo'].label = 'Tipo de Autor'
        # self.filters['autoria__autor__partido'].label = 'Partido do Autor'
        self.filters['relatoria__parlamentar_id'].label = 'Relatoria'

        row1 = to_row(
            [('tipo', 12)])
        row2 = to_row(
            [('numero', 3),
             ('numeracao__numero_materia', 3),
             ('numero_protocolo', 3),
             ('ano', 3)])
        row3 = to_row(
            [('data_apresentacao', 6),
             ('data_publicacao', 6)])
        row4 = to_row(
            [('autoria__autor', 0),
             ('autoria__primeiro_autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])
        row5 = to_row(
            [('autoria__autor__tipo', 12),
             # ('autoria__autor__partido', 6)
             ])
        row6 = to_row(
            [('relatoria__parlamentar_id', 6),
             ('local_origem_externa', 6)])
        row7 = to_row(
            [('tramitacao__unidade_tramitacao_destino', 6),
             ('tramitacao__status', 6)])
        row8 = to_row(
            [('em_tramitacao', 6),
             ('o', 6)])
        row9 = to_row(
            [('materiaassunto__assunto', 6), ('indexacao', 6)])
        row10 = to_row(
            [('ementa', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria'),
                     row1, row2, row3,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row4, row5, row6, row7, row8, row9, row10,
                     form_actions(label='Pesquisar'))
        )

    @property
    def qs(self):
        return qs_override_django_filter(self)


def pega_ultima_tramitacao():
    return Tramitacao.objects.values(
        'materia_id').annotate(data_encaminhamento=Max(
            'data_encaminhamento'),
        id=Max('id')).values_list('id', flat=True)


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
    comissao = forms.ModelChoiceField(
        queryset=Comissao.objects.filter(ativa=True))

    class Meta:
        model = DespachoInicial
        fields = ['comissao']

    def clean(self):
        super(DespachoInicialForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        if DespachoInicial.objects.filter(
            materia=self.instance.materia,
            comissao=self.cleaned_data['comissao'],
        ).exists():
            msg = _('Esse Despacho já foi cadastrado.')
            raise ValidationError(msg)

        return self.cleaned_data


class AutoriaForm(ModelForm):

    tipo_autor = ModelChoiceField(label=_('Tipo Autor'),
                                  required=False,
                                  queryset=TipoAutor.objects.all(),
                                  empty_label=_('Selecione'),)

    data_relativa = forms.DateField(
        widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(AutoriaForm, self).__init__(*args, **kwargs)

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
        model = Autoria
        fields = ['tipo_autor', 'autor', 'primeiro_autor', 'data_relativa']

    def clean(self):
        cd = super(AutoriaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        autorias = Autoria.objects.filter(
            materia=self.instance.materia, autor=cd['autor'])
        pk = self.instance.pk

        if ((not pk and autorias.exists()) or
                (pk and autorias.exclude(pk=pk).exists())):
            raise ValidationError(_('Esse Autor já foi cadastrado.'))

        return cd


class AutoriaMultiCreateForm(Form):

    tipo_autor = ModelChoiceField(label=_('Tipo Autor'),
                                  required=False,
                                  queryset=TipoAutor.objects.all(),
                                  empty_label=_('Selecione'),)

    data_relativa = forms.DateField(
        widget=forms.HiddenInput(), required=False)

    autor = ModelMultipleChoiceField(
        queryset=Autor.objects.all(),
        label=_('Possiveis Autores'),
        required=False,
        widget=CheckboxSelectMultiple)

    autores = ModelMultipleChoiceField(
        queryset=Autor.objects.all(),
        required=False,
        widget=HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row1 = to_row([('tipo_autor', 12), ])

        row2 = to_row([('autor', 12), ])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Autorias'), row1, row2, 'data_relativa', 'autores',
                form_actions(label='Incluir Autores Selecionados')))

        self.fields['autor'].choices = []

    def clean(self):
        cd = super().clean()

        if 'autores' in self.errors:
            del self.errors['autores']

        if 'autor' not in cd or not cd['autor'].exists():
            raise ValidationError(
                _('Ao menos um autor deve ser selecionado para inclusão'))

        return cd


class AcessorioEmLoteFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    class Meta:
        model = MateriaLegislativa
        fields = ['tipo', 'data_apresentacao']

    def __init__(self, *args, **kwargs):
        super(AcessorioEmLoteFilterSet, self).__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters['data_apresentacao'].label = 'Data (Inicial - Final)'
        self.form.fields['tipo'].required = True
        self.form.fields['data_apresentacao'].required = True

        row1 = to_row([('tipo', 12)])
        row2 = to_row([('data_apresentacao', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Documentos Acessórios em Lote'),
                     row1, row2, form_actions(label='Pesquisar')))


class PrimeiraTramitacaoEmLoteFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    class Meta:
        model = MateriaLegislativa
        fields = ['tipo', 'data_apresentacao']

    def __init__(self, *args, **kwargs):
        super(PrimeiraTramitacaoEmLoteFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters['data_apresentacao'].label = 'Data (Inicial - Final)'
        self.form.fields['tipo'].required = True
        self.form.fields['data_apresentacao'].required = False

        row1 = to_row([('tipo', 12)])
        row2 = to_row([('data_apresentacao', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Primeira Tramitação'),
                     row1, row2, form_actions(label='Pesquisar')))


class TramitacaoEmLoteFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    class Meta:
        model = MateriaLegislativa
        fields = ['tipo', 'data_apresentacao', 'tramitacao__status',
                  'tramitacao__unidade_tramitacao_destino']

    def __init__(self, *args, **kwargs):
        super(TramitacaoEmLoteFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters['data_apresentacao'].label = 'Data (Inicial - Final)'
        self.filters['tramitacao__unidade_tramitacao_destino'
                     ].label = 'Unidade Destino (Último Destino)'
        self.form.fields['tipo'].required = True
        self.form.fields['data_apresentacao'].required = False
        self.form.fields['tramitacao__status'].required = True
        self.form.fields[
            'tramitacao__unidade_tramitacao_destino'].required = True

        row1 = to_row([
            ('tipo', 4),
            ('tramitacao__unidade_tramitacao_destino', 4),
            ('tramitacao__status', 4)])
        row2 = to_row([('data_apresentacao', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Tramitação em Lote'),
                     row1, row2, form_actions(label='Pesquisar')))


class TipoProposicaoForm(ModelForm):

    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        label=TipoProposicao._meta.get_field('content_type').verbose_name,
        required=True)

    tipo_conteudo_related_radio = ChoiceWithoutValidationField(
        label="Seleção de Tipo",
        required=False,
        widget=forms.RadioSelect())

    tipo_conteudo_related = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True)

    class Meta:
        model = TipoProposicao
        fields = ['descricao',
                  'content_type',
                  'tipo_conteudo_related_radio',
                  'tipo_conteudo_related',
                  'perfis']

        widgets = {'tipo_conteudo_related': forms.HiddenInput(),
                   'perfis': widgets.CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):

        tipo_select = Fieldset(TipoProposicao._meta.verbose_name,
                               Div(to_column(('descricao', 5)),
                                   to_column(('content_type', 7)),
                                   css_class='clearfix'),
                               to_column(('tipo_conteudo_related_radio', 6)),

                               to_column(('perfis', 6)))

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(tipo_select)

        super(TipoProposicaoForm, self).__init__(*args, **kwargs)

        content_types = ContentType.objects.get_for_models(
            *models_with_gr_for_model(TipoProposicao))

        self.fields['content_type'].choices = [
            (ct.pk, ct) for k, ct in content_types.items()]
        self.fields['content_type'].choices.sort(key=lambda x: str(x[1]))

        if self.instance.pk:
            self.fields[
                'tipo_conteudo_related'].initial = self.instance.object_id

    def clean(self):
        super(TipoProposicaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cd = self.cleaned_data

        content_type = cd['content_type']

        if 'tipo_conteudo_related' not in cd or not cd[
           'tipo_conteudo_related']:
            raise ValidationError(
                _('Seleção de Tipo não definida'))

        if not content_type.model_class().objects.filter(
                pk=cd['tipo_conteudo_related']).exists():
            raise ValidationError(
                _('O Registro definido (%s) não está na base de %s.'
                  ) % (cd['tipo_conteudo_related'], content_type))

        """
        A unicidade de tipo proposição para tipo de conteudo
        foi desabilitada pois existem casos em quem é o procedimento da
        instituição convergir vários tipos de proposição
        para um tipo de matéria.

        unique_value = self._meta.model.objects.filter(
            content_type=content_type, object_id=cd['tipo_conteudo_related'])

        if self.instance.pk:
            unique_value = unique_value.exclude(pk=self.instance.pk)

        unique_value = unique_value.first()

        if unique_value:
            raise ValidationError(
                _('Já existe um Tipo de Proposição (%s) '
                  'que foi defindo como (%s) para (%s)'
                  ) % (unique_value,
                       content_type,
                       unique_value.tipo_conteudo_related))"""

        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=False):

        tipo_proposicao = self.instance

        assert tipo_proposicao.content_type

        tipo_proposicao.tipo_conteudo_related = \
            tipo_proposicao.content_type.model_class(
            ).objects.get(pk=self.cleaned_data['tipo_conteudo_related'])

        return super().save(True)


class TipoProposicaoSelect(Select):

    def render_tipo_option(self, selected_choices, option_value, option_label,
                           data_has_perfil=False):
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return format_html(
            '<option value="{}"{} data-has-perfil={}>{}</option>',
            option_value,
            selected_html,
            str(data_has_perfil),
            force_text(option_label))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []
        output.append(
            self.render_tipo_option(
                selected_choices, '', self.choices.field.empty_label))

        for tipo in self.choices.queryset.all():
            output.append(
                self.render_tipo_option(
                    selected_choices,
                    str(tipo.pk),
                    str(tipo),
                    data_has_perfil=tipo.perfis.exists()))
        return '\n'.join(output)


class ProposicaoForm(forms.ModelForm):

    TIPO_TEXTO_CHOICE = [
        ('D', _('Arquivo Digital')),
        ('T', _('Texto Articulado'))
    ]

    tipo_materia = forms.ModelChoiceField(
        label=TipoMateriaLegislativa._meta.verbose_name,
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione')

    numero_materia = forms.CharField(
        label='Número', required=False)

    ano_materia = forms.CharField(
        label='Ano', required=False)

    tipo_texto = forms.ChoiceField(
        label=_('Tipo do Texto da Proposição'),
        required=False,
        choices=TIPO_TEXTO_CHOICE,
        widget=widgets.RadioSelect())

    materia_de_vinculo = forms.ModelChoiceField(
        queryset=MateriaLegislativa.objects.all(),
        widget=widgets.HiddenInput(),
        required=False)

    receber_recibo = forms.TypedChoiceField(
        choices=YES_NO_CHOICES,
        widget=widgets.HiddenInput(),
        required=False)

    class Meta:
        model = Proposicao
        fields = ['tipo',
                  'receber_recibo',
                  'descricao',
                  'texto_original',
                  'materia_de_vinculo',

                  'tipo_materia',
                  'numero_materia',
                  'ano_materia',
                  'tipo_texto',
                  'hash_code']

        widgets = {
            'descricao': widgets.Textarea(attrs={'rows': 4}),
            'tipo': TipoProposicaoSelect(),
            'hash_code': forms.HiddenInput(), }

    def __init__(self, *args, **kwargs):
        self.texto_articulado_proposicao = sapl.base.models.AppConfig.attr(
            'texto_articulado_proposicao')

        self.receber_recibo = sapl.base.models.AppConfig.attr(
            'receber_recibo_proposicao')

        if not self.texto_articulado_proposicao:
            if 'tipo_texto' in self._meta.fields:
                self._meta.fields.remove('tipo_texto')
        else:
            if 'tipo_texto' not in self._meta.fields:
                self._meta.fields.append('tipo_texto')

        fields = [
            to_column((Fieldset(
                TipoProposicao._meta.verbose_name, Field('tipo')), 12)),
            to_column(
                (Alert('teste',
                       css_class="ementa_materia hidden alert-info",
                       dismiss=False), 12)),
            to_column(('descricao', 12)),

        ]

        if self.texto_articulado_proposicao:
            fields.append(
                to_column((InlineRadios('tipo_texto'), 5)),)

        fields.append(to_column((
            'texto_original', 7 if self.texto_articulado_proposicao else 12)))

        fields.append(to_column((Fieldset(_('Outras informações - Vincular a Matéria Legislativa Existente'),
                     to_column(('tipo_materia', 12)),
                     to_column(('numero_materia', 6)),
                     to_column(('ano_materia', 6))
                     ), 12)),
                     )
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(*fields)

        super(ProposicaoForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['tipo_texto'].initial = ''
            if self.instance.texto_original:
                self.fields['tipo_texto'].initial = 'D'
            if self.texto_articulado_proposicao:
                if self.instance.texto_articulado.exists():
                    self.fields['tipo_texto'].initial = 'T'

            if self.instance.materia_de_vinculo:
                self.fields[
                    'tipo_materia'
                ].initial = self.instance.materia_de_vinculo.tipo
                self.fields[
                    'numero_materia'
                ].initial = self.instance.materia_de_vinculo.numero
                self.fields[
                    'ano_materia'
                ].initial = self.instance.materia_de_vinculo.ano

    def clean_texto_original(self):
        texto_original = self.cleaned_data.get('texto_original', False)
        if texto_original and texto_original.size > MAX_DOC_UPLOAD_SIZE:
            max_size = str(MAX_DOC_UPLOAD_SIZE / (1024 * 1024))
            raise ValidationError(
                    "Arquivo muito grande. ( > {0}MB )".format(max_size))
        return texto_original

    def gerar_hash(self, inst, receber_recibo):

        inst.save()
        if receber_recibo == True:
            inst.hash_code = ''
        else:
            if inst.texto_original:
                inst.hash_code = gerar_hash_arquivo(
                    inst.texto_original.path, str(inst.pk))
            elif inst.texto_articulado.exists():
                ta = inst.texto_articulado.first()
                # FIXME hash para textos articulados
                inst.hash_code = 'P' + ta.hash() + '/' + str(inst.pk)

    def clean(self):
        super(ProposicaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cd = self.cleaned_data

        tm, am, nm = (cd.get('tipo_materia', ''),
                      cd.get('ano_materia', ''),
                      cd.get('numero_materia', ''))

        if tm and am and nm:
            try:
                materia_de_vinculo = MateriaLegislativa.objects.get(
                    tipo_id=tm,
                    ano=am,
                    numero=nm
                )
            except ObjectDoesNotExist:
                raise ValidationError(_('Matéria Vinculada não existe!'))
            else:
                cd['materia_de_vinculo'] = materia_de_vinculo
        return cd

    def save(self, commit=True):
        cd = self.cleaned_data
        inst = self.instance
        receber_recibo = AppConfig.objects.last().receber_recibo_proposicao

        if inst.pk:
            if 'tipo_texto' in cd:

                if cd['tipo_texto'] == 'T' and inst.texto_original:
                    inst.texto_original.delete()

                elif cd['tipo_texto'] != 'T':
                    inst.texto_articulado.all().delete()

                    if 'texto_original' in cd and\
                            not cd['texto_original'] and \
                            inst.texto_original:
                        inst.texto_original.delete()
            self.gerar_hash(inst, receber_recibo)


            return super().save(commit)

        inst.ano = timezone.now().year
        numero__max = Proposicao.objects.filter(
            autor=inst.autor,
            ano=timezone.now().year).aggregate(Max('numero_proposicao'))
        numero__max = numero__max['numero_proposicao__max']
        inst.numero_proposicao = (
            numero__max + 1) if numero__max else 1

        self.gerar_hash(inst, receber_recibo)

        inst.save()

        return inst


class DevolverProposicaoForm(forms.ModelForm):

    justificativa_devolucao = forms.CharField(
        required=False, widget=widgets.Textarea(attrs={'rows': 5}))

    class Meta:
        model = Proposicao
        fields = [
            'justificativa_devolucao',
        ]

    def __init__(self, *args, **kwargs):

        # esta chamada isola o __init__ de ProposicaoForm
        super(DevolverProposicaoForm, self).__init__(*args, **kwargs)
        fields = []

        fields.append(
            Fieldset(
                _('Registro de Devolução'),
                to_column(('justificativa_devolucao', 12)),
                to_column(
                    (form_actions(label=_('Devolver'),
                                  name='devolver',
                                  css_class='btn-danger pull-right'), 12)
                )
            )
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(*fields)

    def clean(self):
        super(DevolverProposicaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cd = self.cleaned_data

        if 'justificativa_devolucao' not in cd or\
                not cd['justificativa_devolucao']:
            # TODO Implementar notificação ao autor por email
            raise ValidationError(
                _('Adicione uma Justificativa para devolução.'))
        return cd

    @transaction.atomic
    def save(self, commit=False):
        cd = self.cleaned_data

        self.instance.data_devolucao = timezone.now()
        self.instance.data_recebimento = None
        self.instance.data_envio = None
        self.instance.save()

        if self.instance.texto_articulado.exists():
            ta = self.instance.texto_articulado.first()
            ta.privacidade = STATUS_TA_PRIVATE
            ta.editing_locked = False
            ta.save()

        self.instance.results = {
            'messages': {
                'success': [_('Devolução efetuada com sucesso.'), ]
            },
            'url': reverse('sapl.materia:receber-proposicao')
        }
        return self.instance


class ConfirmarProposicaoForm(ProposicaoForm):

    tipo_readonly = forms.CharField(
        label=TipoProposicao._meta.verbose_name,
        required=False, widget=widgets.TextInput(
            attrs={'readonly': 'readonly'}))

    autor_readonly = forms.CharField(
        label=Autor._meta.verbose_name,
        required=False, widget=widgets.TextInput(
            attrs={'readonly': 'readonly'}))

    regime_tramitacao = forms.ModelChoiceField(
        required=False, queryset=RegimeTramitacao.objects.all())

    gerar_protocolo = forms.ChoiceField(
        required=False,
        label=_(
            'Gerar Protocolo na incorporação?'),
        choices=YES_NO_CHOICES,
        widget=widgets.RadioSelect())

    numero_de_paginas = forms.IntegerField(required=False, min_value=0,
                                           label=_('Número de Páginas'),)

    class Meta:
        model = Proposicao
        fields = [
            'data_envio',
            'descricao',
            'gerar_protocolo',
            'numero_de_paginas'
        ]
        widgets = {
            'descricao': widgets.Textarea(
                attrs={'readonly': 'readonly', 'rows': 4}),
            'data_envio':  widgets.DateTimeInput(
                attrs={'readonly': 'readonly'}),

        }

    def __init__(self, *args, **kwargs):

        self.proposicao_incorporacao_obrigatoria = \
            sapl.base.models.AppConfig.attr(
                'proposicao_incorporacao_obrigatoria')

        if self.proposicao_incorporacao_obrigatoria != 'C':
            if 'gerar_protocolo' in self._meta.fields:
                self._meta.fields.remove('gerar_protocolo')
        else:
            if 'gerar_protocolo' not in self._meta.fields:
                self._meta.fields.append('gerar_protocolo')

        if self.proposicao_incorporacao_obrigatoria == 'N':
            if 'numero_de_paginas' in self._meta.fields:
                self._meta.fields.remove('numero_de_paginas')
        else:
            if 'numero_de_paginas' not in self._meta.fields:
                self._meta.fields.append('numero_de_paginas')

        self.instance = kwargs.get('instance', None)
        if not self.instance:
            raise ValueError(_('Erro na Busca por proposição a incorporar'))

        if self.instance.tipo.content_type.model_class() == TipoDocumento:
            if 'numero_de_paginas' in self._meta.fields:
                self._meta.fields.remove('numero_de_paginas')
            if 'gerar_protocolo' in self._meta.fields:
                self._meta.fields.remove('gerar_protocolo')
            if 'regime_tramitacao' in self._meta.fields:
                self._meta.fields.remove('regime_tramitacao')

        # esta chamada isola o __init__ de ProposicaoForm
        super(ProposicaoForm, self).__init__(*args, **kwargs)

        fields = [
            Fieldset(
                _('Dados Básicos'),
                to_column(('tipo_readonly', 4)),
                to_column(('data_envio', 3)),
                to_column(('autor_readonly', 5)),
                to_column(('descricao', 12)))]

        fields.append(
            Fieldset(_('Vinculado a Matéria Legislativa'),
                     to_column(('tipo_materia', 3)),
                     to_column(('numero_materia', 2)),
                     to_column(('ano_materia', 2)),
                     to_column(
                (Alert(_('O responsável pela incorporação pode '
                         'alterar a anexação. Limpar os campos '
                         'de Vinculação gera um %s independente '
                         'sem anexação se for possível para esta '
                         'Proposição. Não sendo, a rotina de incorporação '
                         'não permitirá estes campos serem vazios.'
                         ) % self.instance.tipo.content_type,
                       css_class="alert-info",
                       dismiss=False), 5)),
                to_column(
                (Alert('',
                       css_class="ementa_materia hidden alert-info",
                       dismiss=False), 12))))

        itens_incorporacao = []
        if self.instance.tipo.content_type.model_class() == \
                TipoMateriaLegislativa:
            itens_incorporacao = [to_column(('regime_tramitacao', 4))]

            if self.proposicao_incorporacao_obrigatoria == 'C':
                itens_incorporacao.append(to_column((InlineRadios(
                    'gerar_protocolo'), 4)))

            if self.proposicao_incorporacao_obrigatoria != 'N':
                itens_incorporacao.append(to_column(('numero_de_paginas', 4)))

        itens_incorporacao.append(
            to_column(
                (form_actions(label=_('Incorporar'),
                              name='incorporar'), 12)
            )
        )

        fields.append(
            Fieldset(_('Registro de Incorporação'), *itens_incorporacao))

        self.helper = FormHelper()
        self.helper.layout = Layout(*fields)

        self.fields['tipo_readonly'].initial = self.instance.tipo.descricao
        self.fields['autor_readonly'].initial = str(self.instance.autor)

        if self.instance.materia_de_vinculo:
            self.fields[
                'tipo_materia'
            ].initial = self.instance.materia_de_vinculo.tipo
            self.fields[
                'numero_materia'
            ].initial = self.instance.materia_de_vinculo.numero
            self.fields[
                'ano_materia'
            ].initial = self.instance.materia_de_vinculo.ano

        if self.proposicao_incorporacao_obrigatoria == 'C':
            self.fields['gerar_protocolo'].initial = True

    def clean(self):
        super(ConfirmarProposicaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        numeracao = sapl.base.models.AppConfig.attr('sequencia_numeracao')

        if not numeracao:
            raise ValidationError("A sequência de numeração (por ano ou geral)"
                                  " não foi configurada para a aplicação em "
                                  "tabelas auxiliares")

        cd = ProposicaoForm.clean(self)

        if self.instance.tipo.content_type.model_class() ==\
                TipoMateriaLegislativa:
            if 'regime_tramitacao' not in cd or\
                    not cd['regime_tramitacao']:
                raise ValidationError(
                    _('Regime de Tramitação deve ser informado.'))

        elif self.instance.tipo.content_type.model_class(
        ) == TipoDocumento and not cd['materia_de_vinculo']:

            raise ValidationError(
                _('Documentos não podem ser incorporados sem definir '
                  'para qual Matéria Legislativa ele se destina.'))

        return cd

    @transaction.atomic
    def save(self, commit=False):
        # TODO Implementar workflow entre protocolo e autores
        cd = self.cleaned_data

        self.instance.justificativa_devolucao = ''
        self.instance.data_devolucao = None
        self.instance.data_recebimento = timezone.now()
        self.instance.materia_de_vinculo = cd['materia_de_vinculo']

        if self.instance.texto_articulado.exists():
            ta = self.instance.texto_articulado.first()
            ta.privacidade = STATUS_TA_IMMUTABLE_PUBLIC
            ta.editing_locked = True
            ta.save()

        self.instance.save()

        """
        TipoProposicao possui conteúdo genérico para a modelegam de tipos
        relacionados e, a esta modelagem, qual o objeto que está associado.
        Porem, cada registro a ser gerado pode possuir uma estrutura diferente,
        é os casos básicos já implementados,
        TipoDocumento e TipoMateriaLegislativa, que são modelos utilizados
        em DocumentoAcessorio e MateriaLegislativa geradas,
        por sua vez a partir de uma Proposição.
        Portanto para estas duas e para outras implementações que possam surgir
        possuindo com matéria prima uma Proposição, dada sua estrutura,
        deverá contar também com uma implementação particular aqui no código
        abaixo.
        """
        self.instance.results = {
            'messages': {
                'success': [_('Proposição incorporada com sucesso'), ]
            },
            'url': reverse('sapl.materia:receber-proposicao')
        }
        proposicao = self.instance
        conteudo_gerado = None

        if self.instance.tipo.content_type.model_class(
        ) == TipoMateriaLegislativa:

            numeracao = None
            try:
                numeracao = sapl.base.models.AppConfig.objects.last(
                ).sequencia_numeracao
            except AttributeError:
                pass

            tipo = self.instance.tipo.tipo_conteudo_related
            if tipo.sequencia_numeracao:
                numeracao = tipo.sequencia_numeracao
            ano = timezone.now().year
            if numeracao == 'A':
                numero = MateriaLegislativa.objects.filter(
                    ano=ano, tipo=tipo).aggregate(Max('numero'))
            elif numeracao == 'L':
                legislatura = Legislatura.objects.filter(
                    data_inicio__year__lte=ano,
                    data_fim__year__gte=ano).first()
                data_inicio = legislatura.data_inicio
                data_fim = legislatura.data_fim
                numero = MateriaLegislativa.objects.filter(
                    data_apresentacao__gte=data_inicio,
                    data_apresentacao__lte=data_fim,
                    tipo=tipo).aggregate(
                    Max('numero'))
            elif numeracao == 'U':
                numero = MateriaLegislativa.objects.filter(tipo=tipo).aggregate(Max('numero'))

            if numeracao is None:
                numero['numero__max'] = 0

            max_numero = numero['numero__max'] + 1 if numero['numero__max'] else 1

            # dados básicos
            materia = MateriaLegislativa()
            materia.numero = max_numero
            materia.tipo = tipo
            materia.ementa = proposicao.descricao
            materia.ano = ano
            materia.data_apresentacao = timezone.now()
            materia.em_tramitacao = True
            materia.regime_tramitacao = cd['regime_tramitacao']

            if proposicao.texto_original:
                materia.texto_original = File(
                    proposicao.texto_original,
                    os.path.basename(proposicao.texto_original.path))

            materia.save()
            conteudo_gerado = materia

            if proposicao.texto_articulado.exists():
                ta = proposicao.texto_articulado.first()
                ta_materia = ta.clone_for(materia)
                ta_materia.editing_locked = True
                ta_materia.privacidade = STATUS_TA_IMMUTABLE_PUBLIC
                ta_materia.save()

            self.instance.results['messages']['success'].append(_(
                'Matéria Legislativa registrada com sucesso (%s)'
            ) % str(materia))

            # autoria
            autoria = Autoria()
            autoria.autor = proposicao.autor
            autoria.materia = materia
            autoria.primeiro_autor = True
            autoria.save()

            self.instance.results['messages']['success'].append(_(
                'Autoria registrada para (%s)'
            ) % str(autoria.autor))

            # Matéria de vinlculo
            if proposicao.materia_de_vinculo:
                anexada = Anexada()
                anexada.materia_principal = proposicao.materia_de_vinculo
                anexada.materia_anexada = materia
                anexada.data_anexacao = timezone.now()
                anexada.save()

                self.instance.results['messages']['success'].append(_(
                    'Matéria anexada a (%s)'
                ) % str(anexada.materia_principal))

            self.instance.results['url'] = reverse(
                'sapl.materia:materialegislativa_detail',
                kwargs={'pk': materia.pk})

        elif self.instance.tipo.content_type.model_class() == TipoDocumento:

            # dados básicos
            doc = DocumentoAcessorio()
            doc.materia = proposicao.materia_de_vinculo
            doc.autor = str(proposicao.autor)
            doc.tipo = proposicao.tipo.tipo_conteudo_related

            doc.ementa = proposicao.descricao
            """ FIXME verificar questão de nome e data de documento,
            doc acessório. Possivelmente pode possuir data anterior a
            data de envio e/ou recebimento dada a incorporação.
            """
            doc.nome = str(proposicao.tipo.tipo_conteudo_related)[:30]
            doc.data = proposicao.data_envio

            doc.arquivo = proposicao.texto_original = File(
                proposicao.texto_original,
                os.path.basename(proposicao.texto_original.path))
            doc.save()
            conteudo_gerado = doc

            self.instance.results['messages']['success'].append(_(
                'Documento Acessório registrado com sucesso e anexado (%s)'
            ) % str(doc.materia))

            self.instance.results['url'] = reverse(
                'sapl.materia:documentoacessorio_detail',
                kwargs={'pk': doc.pk})

        proposicao.conteudo_gerado_related = conteudo_gerado
        proposicao.save()

        if self.instance.tipo.content_type.model_class() == TipoDocumento:
            return self.instance

        # Nunca gerar protocolo
        if self.proposicao_incorporacao_obrigatoria == 'N':
            return self.instance

        # ocorre se proposicao_incorporacao_obrigatoria == 'C' (condicional)
        # and gerar_protocolo == False
        if 'gerar_protocolo' not in cd or cd['gerar_protocolo'] == 'False':
            return self.instance

        # resta a opção proposicao_incorporacao_obrigatoria == 'C'
        # and gerar_protocolo == True
        # ou, proposicao_incorporacao_obrigatoria == 'O'
        # que são idênticas.

        """
        apesar de TipoProposicao estar com conteudo e tipo conteudo genérico,
        aqui na incorporação de proposições, para gerar protocolo, cada caso
        possível de conteudo em tipo de proposição deverá ser tratado
        isoladamente justamente por Protocolo não estar generalizado com
        GenericForeignKey
        """

        numeracao = sapl.base.models.AppConfig.attr('sequencia_numeracao')
        if numeracao == 'A':
            nm = Protocolo.objects.filter(
                ano=timezone.now().year).aggregate(Max('numero'))
        elif numeracao == 'L':
            legislatura = Legislatura.objects.filter(
                data_inicio__year__lte=timezone.now().year,
                data_fim__year__gte=timezone.now().year).first()
            data_inicio = legislatura.data_inicio
            data_fim = legislatura.data_fim
            nm = MateriaLegislativa.objects.filter(
                data_apresentacao__gte=data_inicio,
                data_apresentacao__lte=data_fim,
                tipo=tipo).aggregate(Max('numero'))

        else:
            # numeracao == 'U' ou não informada
            nm = Protocolo.objects.all().aggregate(Max('numero'))

        protocolo = Protocolo()
        protocolo.numero = (nm['numero__max'] + 1) if nm['numero__max'] else 1
        protocolo.ano = timezone.now().year

        protocolo.tipo_protocolo = '1'

        protocolo.interessado = str(proposicao.autor)
        protocolo.autor = proposicao.autor
        protocolo.assunto_ementa = proposicao.descricao
        protocolo.numero_paginas = cd['numero_de_paginas']
        protocolo.anulado = False

        if self.instance.tipo.content_type.model_class(
        ) == TipoMateriaLegislativa:
            protocolo.tipo_materia = proposicao.tipo.tipo_conteudo_related
            protocolo.tipo_processo = '1'
        elif self.instance.tipo.content_type.model_class() == TipoDocumento:
            protocolo.tipo_documento = proposicao.tipo.tipo_conteudo_related
            protocolo.tipo_processo = '0'

        protocolo.save()

        self.instance.results['messages']['success'].append(_(
            'Protocolo realizado com sucesso'))

        # FIXME qdo protocoloadm estiver homologado, verifique a necessidade
        # de redirecionamento para o protocolo.
        # complete e libere código abaixo para tal.

        """
        self.instance.results['url'] = reverse(
            'sapl.protocoloadm:...',
            kwargs={'pk': protocolo.pk})
        """
        conteudo_gerado.numero_protocolo = protocolo.numero
        conteudo_gerado.save()

        return self.instance


class MateriaAssuntoForm(ModelForm):

    class Meta:
        model = MateriaAssunto
        fields = ['materia', 'assunto']

        widgets = {'materia': forms.HiddenInput()}


class EtiquetaPesquisaForm(forms.Form):
    tipo_materia = forms.ModelChoiceField(
        label=TipoMateriaLegislativa._meta.verbose_name,
        queryset=TipoMateriaLegislativa.objects.all(),
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

    processo_inicial = forms.IntegerField(
        label='Processo Inicial',
        required=False)

    processo_final = forms.IntegerField(
        label='Processo Final',
        required=False)

    def __init__(self, *args, **kwargs):
        super(EtiquetaPesquisaForm, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('tipo_materia', 6),
             ('data_inicial', 3),
             ('data_final', 3)])

        row2 = to_row(
            [('processo_inicial', 6),
             ('processo_final', 6)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                ('Formulário de Etiqueta'),
                row1, row2,
                form_actions(label='Pesquisar')
            )
        )

    def clean(self):
        super(EtiquetaPesquisaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        # Verifica se algum campo de data foi preenchido
        if cleaned_data['data_inicial'] or cleaned_data['data_final']:
            # Então verifica se o usuário preencheu o Incial e mas não
            # preencheu o Final, ou vice-versa
            if (not cleaned_data['data_inicial'] or
                    not cleaned_data['data_final']):
                raise ValidationError(_(
                    'Caso pesquise por data, os campos de Data Incial e ' +
                    'Data Final devem ser preenchidos obrigatoriamente'))
            # Caso tenha preenchido, verifica se a data final é maior que
            # a inicial
            elif cleaned_data['data_final'] < cleaned_data['data_inicial']:
                raise ValidationError(_(
                    'A Data Final não pode ser menor que a Data Inicial'))

        # O mesmo processo anterior é feito com o processo
        if (cleaned_data['processo_inicial'] or
                cleaned_data['processo_final']):
            if (not cleaned_data['processo_inicial'] or
                    not cleaned_data['processo_final']):
                raise ValidationError(_(
                    'Caso pesquise por número de processo, os campos de ' +
                    'Processo Inicial e Processo Final ' +
                    'devem ser preenchidos obrigatoriamente'))
            elif (cleaned_data['processo_final'] <
                  cleaned_data['processo_inicial']):
                raise ValidationError(_(
                    'O processo final não pode ser menor que o inicial'))

        return cleaned_data


class FichaPesquisaForm(forms.Form):
    tipo_materia = forms.ModelChoiceField(
        label=TipoMateriaLegislativa._meta.verbose_name,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione')

    data_inicial = forms.DateField(
        label='Data Inicial',
        widget=forms.DateInput(format='%d/%m/%Y')
    )

    data_final = forms.DateField(
        label='Data Final',
        widget=forms.DateInput(format='%d/%m/%Y')
    )

    def __init__(self, *args, **kwargs):
        super(FichaPesquisaForm, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('tipo_materia', 6),
             ('data_inicial', 3),
             ('data_final', 3)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                ('Formulário de Ficha'),
                row1,
                form_actions(label='Pesquisar')
            )
        )

    def clean(self):
        super(FichaPesquisaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        if cleaned_data['data_final'] < cleaned_data['data_inicial']:
            raise ValidationError(_(
                'A Data Final não pode ser menor que a Data Inicial'))

        return cleaned_data


class FichaSelecionaForm(forms.Form):
    materia = forms.ModelChoiceField(
        widget=forms.RadioSelect,
        queryset=MateriaLegislativa.objects.all(),
        label='')

    def __init__(self, *args, **kwargs):
        super(FichaSelecionaForm, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('materia', 12)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                ('Selecione a ficha que deseja imprimir'),
                row1,
                form_actions(label='Gerar Impresso')
            )
        )


class ExcluirTramitacaoEmLote(forms.Form):

    data_tramitacao = forms.DateField(required=True,
                             label=_('Data da Tramitação'))

    unidade_tramitacao_local = forms.ModelChoiceField(label=_('Unidade Local'),
                                  required=True,
                                  queryset=UnidadeTramitacao.objects.all(),
                                  empty_label='------')

    unidade_tramitacao_destino = forms.ModelChoiceField(label=_('Unidade Destino'),
                                  required=True,
                                  queryset=UnidadeTramitacao.objects.all(),
                                  empty_label='------')

    status = forms.ModelChoiceField(label=_('Status'),
                                  required=True,
                                  queryset=StatusTramitacao.objects.all(),
                                  empty_label='------')

    def clean(self):
        super(ExcluirTramitacaoEmLote, self).clean()

        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        data_tramitacao = cleaned_data['data_tramitacao']
        unidade_tramitacao_local = cleaned_data['unidade_tramitacao_local']
        unidade_tramitacao_destino = cleaned_data['unidade_tramitacao_destino']
        status = cleaned_data['status']

        tramitacao_set = Tramitacao.objects.filter(data_tramitacao=data_tramitacao,
                                                           unidade_tramitacao_local=unidade_tramitacao_local,
                                                           unidade_tramitacao_destino=unidade_tramitacao_destino,
                                                           status=status)
        if not tramitacao_set.exists():
            raise forms.ValidationError(
                _("Não existem tramitações com os dados informados."))

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(ExcluirTramitacaoEmLote, self).__init__(*args, **kwargs)

        row1 = to_row(
            [('data_tramitacao', 6),
             ('status', 6),])
        row2 = to_row(
            [('unidade_tramitacao_local', 6),
             ('unidade_tramitacao_destino', 6)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Dados das Tramitações'),
                     row1,
                     row2,
                     HTML("&nbsp;"),
                     form_actions(label='Excluir')
                     )
        )
