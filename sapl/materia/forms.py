from datetime import datetime

import django_filters
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Column, Fieldset, Layout
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models, transaction
from django.db.models import Max
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from sapl.comissoes.models import Comissao
from sapl.crispy_layout_mixin import form_actions, to_row
from sapl.norma.models import (LegislacaoCitada, NormaJuridica,
                               TipoNormaJuridica)
from sapl.settings import MAX_DOC_UPLOAD_SIZE
from sapl.utils import (RANGE_ANOS, RangeWidgetOverride, autor_label,
                        autor_modal)

from .models import (AcompanhamentoMateria, Anexada, Autor, Autoria,
                     DespachoInicial, DocumentoAcessorio, MateriaLegislativa,
                     Numeracao, Proposicao, Relatoria, TipoMateriaLegislativa,
                     Tramitacao, UnidadeTramitacao)

ANO_CHOICES = [('', '---------')] + RANGE_ANOS


def em_tramitacao():
    return [('', 'Tanto Faz'),
            (True, 'Sim'),
            (False, 'Não')]


class ConfirmarProposicaoForm(ModelForm):

    class Meta:
        model = Proposicao
        exclude = ['texto_original', 'descricao', 'tipo']


class ReceberProposicaoForm(ModelForm):
    cod_hash = forms.CharField(label='Código do Documento', required=True)

    class Meta:
        model = Proposicao
        exclude = ['texto_original', 'descricao', 'tipo']

    def __init__(self, *args, **kwargs):
        row1 = to_row([('cod_hash', 12)])
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Incorporar Proposição'), row1,
                form_actions(save_label='Buscar Proposição')
            )
        )
        super(ReceberProposicaoForm, self).__init__(*args, **kwargs)


class UnidadeTramitacaoForm(ModelForm):

    class Meta:
        model = UnidadeTramitacao
        fields = ['comissao', 'orgao', 'parlamentar']

    def clean(self):
        cleaned_data = self.cleaned_data

        for key in list(cleaned_data.keys()):
            if cleaned_data[key] is None:
                del cleaned_data[key]

        if len(cleaned_data) != 1:
            msg = _('Somente um campo deve preenchido!')
            raise ValidationError(msg)
        return cleaned_data


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

    def clean_data_envio(self):
        data_envio = self.cleaned_data.get('data_envio') or None
        if (not data_envio) and len(self.initial) > 1:
            data_envio = datetime.now()
        return data_envio

    def clean(self):
        cleaned_data = self.cleaned_data
        if 'tipo' in cleaned_data:
            if cleaned_data['tipo'].descricao == 'Parecer':
                if self.instance.materia:
                    cleaned_data['materia'] = self.instance.materia
                else:
                    try:
                        materia = MateriaLegislativa.objects.get(
                            tipo_id=cleaned_data['tipo_materia'],
                            ano=cleaned_data['ano_materia'],
                            numero=cleaned_data['numero_materia'])
                    except ObjectDoesNotExist:
                        msg = _('Matéria adicionada não existe!')
                        raise ValidationError(msg)
                    else:
                        cleaned_data['materia'] = materia
        return cleaned_data

    def save(self, commit=False):
        proposicao = super(ProposicaoForm, self).save(commit)
        if 'materia' in self.cleaned_data:
            proposicao.materia = self.cleaned_data['materia']
        proposicao.save()
        return proposicao

    class Meta:
        model = Proposicao
        fields = ['tipo', 'data_envio', 'descricao', 'texto_original', 'autor']
        widgets = {'autor': forms.HiddenInput()}


class AcompanhamentoMateriaForm(ModelForm):

    class Meta:
        model = AcompanhamentoMateria
        fields = ['email']

    def __init__(self, *args, **kwargs):

        row1 = to_row([('email', 10)])

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

    class Meta:
        model = DocumentoAcessorio
        fields = ['tipo', 'nome', 'data', 'autor', 'ementa', 'arquivo']
        widgets = {'autor': forms.HiddenInput()}

    def clean_autor(self):
        autor_field = self.cleaned_data['autor']
        try:
            int(autor_field)
        except ValueError:
            return autor_field
        else:
            if autor_field:
                return str(Autor.objects.get(id=autor_field))


class RelatoriaForm(ModelForm):

    class Meta:
        model = Relatoria
        fields = ['data_designacao_relator', 'comissao', 'parlamentar',
                  'data_destituicao_relator', 'tipo_fim_relatoria']

        widgets = {'comissao': forms.Select(attrs={'disabled': 'disabled'})}

    def clean(self):
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

    def clean(self):

        if 'data_encaminhamento' in self.data:
            data_enc_form = self.cleaned_data['data_encaminhamento']
        if 'data_fim_prazo' in self.data:
            data_prazo_form = self.cleaned_data['data_fim_prazo']
        if 'data_tramitacao' in self.data:
            data_tram_form = self.cleaned_data['data_tramitacao']

        if self.errors:
            return self.errors

        ultima_tramitacao = Tramitacao.objects.filter(
            materia_id=self.instance.materia_id).exclude(
            id=self.instance.id).last()

        if not self.instance.data_tramitacao:

            if ultima_tramitacao:
                destino = ultima_tramitacao.unidade_tramitacao_destino
                if (destino != self.cleaned_data['unidade_tramitacao_local']):
                    msg = _('A origem da nova tramitação deve ser igual ao '
                            'destino  da última adicionada!')
                    raise ValidationError(msg)

            if self.cleaned_data['data_tramitacao'] > datetime.now().date():
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

        return self.cleaned_data


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
        local = self.instance.unidade_tramitacao_local
        data_tram = self.instance.data_tramitacao

        self.cleaned_data['data_tramitacao'] = data_tram
        self.cleaned_data['unidade_tramitacao_local'] = local
        return super(TramitacaoUpdateForm, self).clean()


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
        if self.errors:
            return self.errors

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

        if LegislacaoCitada.objects.filter(
            materia=self.instance.materia,
            norma=cleaned_data['norma']
        ).exists():
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
                  'autoria__autor__partido',
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
        self.filters['autoria__autor__partido'].label = 'Partido do Autor'
        self.filters['relatoria__parlamentar_id'].label = 'Relatoria'

        row1 = to_row(
            [('tipo', 12)])
        row2 = to_row(
            [('numero', 4),
             ('ano', 4),
             ('numero_protocolo', 4)])
        row3 = to_row(
            [('data_apresentacao', 6),
             ('data_publicacao', 6)])
        row4 = to_row(
            [('autoria__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])
        row5 = to_row(
            [('autoria__autor__tipo', 6),
             ('autoria__autor__partido', 6)])
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
            [('ementa', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria'),
                     row1, row2, row3,
                     HTML(autor_label),
                     HTML(autor_modal),
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
        fields = ['autor', 'primeiro_autor']

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


class AutorForm(ModelForm):
    senha = forms.CharField(
        max_length=20,
        label=_('Senha'),
        required=True,
        widget=forms.PasswordInput())

    senha_confirma = forms.CharField(
        max_length=20,
        label=_('Confirmar Senha'),
        required=True,
        widget=forms.PasswordInput())

    confirma_email = forms.EmailField(
        required=True,
        label=_('Confirmar Email'))

    username = forms.CharField(
        required=True,
        max_length=50
    )

    class Meta:
        model = Autor
        fields = ['username',
                  'senha',
                  'email',
                  'nome',
                  'tipo',
                  'cargo']
        widgets = {'nome': forms.HiddenInput()}

    def valida_igualdade(self, texto1, texto2, msg):
        if texto1 != texto2:
            raise ValidationError(msg)
        return True

    def valida_email_existente(self):
        return get_user_model().objects.filter(
            email=self.cleaned_data['email']).exists()

    def clean(self):

        if 'username' not in self.cleaned_data:
            raise ValidationError(_('Favor informar o username'))

        if ('senha' not in self.cleaned_data or
                'senha_confirma' not in self.cleaned_data):
            raise ValidationError(_('Favor informar as senhas'))

        msg = _('As senhas não conferem.')
        self.valida_igualdade(
            self.cleaned_data['senha'],
            self.cleaned_data['senha_confirma'],
            msg)

        if ('email' not in self.cleaned_data or
                'confirma_email' not in self.cleaned_data):
            raise ValidationError(_('Favor informar endereços de email'))

        msg = _('Os emails não conferem.')
        self.valida_igualdade(
            self.cleaned_data['email'],
            self.cleaned_data['confirma_email'],
            msg)

        email_existente = self.valida_email_existente()

        if (Autor.objects.filter(
           username=self.cleaned_data['username']).exists()):
            raise ValidationError(_('Já existe um autor para este usuário'))

        if email_existente:
            msg = _('Este email já foi cadastrado.')
            raise ValidationError(msg)

        try:
            validate_password(self.cleaned_data['senha'])
        except ValidationError as error:
            raise ValidationError(error)

        try:
            User.objects.get(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'])
        except ObjectDoesNotExist:
            msg = _('Este nome de usuario não está cadastrado. ' +
                    'Por favor, cadastre-o no Administrador do ' +
                    'Sistema antes de adicioná-lo como Autor')
            raise ValidationError(msg)

        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=False):

        autor = super(AutorForm, self).save(commit)

        u = User.objects.get(
            username=autor.username,
            email=autor.email)

        u.set_password(self.cleaned_data['senha'])
        u.is_active = False
        u.save()

        autor.user = u

        autor.save()

        grupo = Group.objects.filter(name='Autor')[0]
        u.groups.add(grupo)

        return autor


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
                     row1, row2, form_actions(save_label='Pesquisar')))


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
        self.form.fields['data_apresentacao'].required = True

        row1 = to_row([('tipo', 12)])
        row2 = to_row([('data_apresentacao', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Primeira Tramitação'),
                     row1, row2, form_actions(save_label='Pesquisar')))


class TramitacaoEmLoteFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    class Meta:
        model = MateriaLegislativa
        fields = ['tipo', 'data_apresentacao',
                  'tramitacao__unidade_tramitacao_local', 'tramitacao__status']

    def __init__(self, *args, **kwargs):
        super(TramitacaoEmLoteFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters['data_apresentacao'].label = 'Data (Inicial - Final)'
        self.form.fields['tipo'].required = True
        self.form.fields['data_apresentacao'].required = True
        self.form.fields['tramitacao__status'].required = True
        self.form.fields[
            'tramitacao__unidade_tramitacao_local'].required = True

        row1 = to_row([
            ('tipo', 4),
            ('tramitacao__unidade_tramitacao_local', 4),
            ('tramitacao__status', 4)])
        row2 = to_row([('data_apresentacao', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Tramitação em Lote'),
                     row1, row2, form_actions(save_label='Pesquisar')))
