from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Fieldset, Layout, Field, Div, Row
from crispy_forms.templatetags.crispy_forms_field import css_class
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.contrib.contenttypes.fields import GenericRel
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models, transaction
from django.forms import ModelForm, widgets
from django.utils.translation import ugettext_lazy as _
import django_filters

from sapl.base.models import Autor, TipoAutor
from sapl.crispy_layout_mixin import form_actions, to_row, SaplFormLayout,\
    to_column
from sapl.materia.models import MateriaLegislativa
from sapl.sessao.models import SessaoPlenaria
from sapl.settings import MAX_IMAGE_UPLOAD_SIZE
from sapl.utils import (RANGE_ANOS, ImageThumbnailFileInput,
                        RangeWidgetOverride, autor_label, autor_modal)

from .models import AppConfig, CasaLegislativa


class TipoAutorForm(ModelForm):

    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        label=TipoAutor._meta.get_field('content_type').verbose_name,
        required=False)

    class Meta:
        model = TipoAutor
        fields = ['descricao',
                  'content_type', ]

    def __init__(self, *args, **kwargs):

        super(TipoAutorForm, self).__init__(*args, **kwargs)

        # Models que apontaram uma GenericRelation com Autor
        models_of_generic_relations = list(map(
            lambda x: x.related_model,
            filter(
                lambda obj: obj.is_relation and
                hasattr(obj, 'field') and
                isinstance(obj, GenericRel),
                Autor._meta.get_fields(include_hidden=True))
        ))

        content_types = ContentType.objects.get_for_models(
            *models_of_generic_relations)

        self.fields['content_type'].choices = [
            ('', _('Outros (Especifique)'))] + [
                (ct.pk, ct) for key, ct in content_types.items()]


class AutorForm(ModelForm):
    """senha = forms.CharField(
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
    )"""

    q = forms.CharField(
        max_length=50, required=False,
        label='Pesquise o nome do Autor com o '
        'tipo Selecionado e marque o escolhido.')
    autor_related = forms.ChoiceField(label='',
                                      required=False,
                                      widget=forms.RadioSelect())

    class Meta:
        model = Autor
        fields = ['tipo',
                  'nome',
                  'autor_related',
                  'q']

    def __init__(self, *args, **kwargs):

        autor_related = Div(

            FieldWithButtons(
                Field('q',
                      placeholder=_('Pesquisar por possíveis autores para '
                                    'o Tipo de Autor selecionado.')),
                StrictButton(
                    _('Filtrar'), css_class='btn-default btn-filtrar-autor',
                    type='button')),
            Field('autor_related'),
            css_class='hidden',
            data_action='create',
            data_application='AutorSearch',
            data_field='autor_related')

        row1 = to_row([
            ('tipo', 4),
            ('nome', 8),
            (autor_related, 8),

        ])

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(row1)

        super(AutorForm, self).__init__(*args, **kwargs)

        self.fields['autor_related'].choices = []
        if self.instance and self.instance.autor_related:
            self.fields['autor_related'].choices = [
                (self.instance.autor_related.pk,
                 self.instance.autor_related)]

    def valida_igualdade(self, texto1, texto2, msg):
        if texto1 != texto2:
            raise ValidationError(msg)
        return True

    def valida_email_existente(self):
        return get_user_model().objects.filter(
            email=self.cleaned_data['email']).exists()

    def clea(self):

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
            get_user_model().objects.get(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'])
        except ObjectDoesNotExist:
            msg = _('Este nome de usuario não está cadastrado. ' +
                    'Por favor, cadastre-o no Administrador do ' +
                    'Sistema antes de adicioná-lo como Autor')
            raise ValidationError(msg)

        return self.cleaned_data

    @transaction.atomic
    def sav(self, commit=False):

        autor = super(AutorForm, self).save(commit)

        u = get_user_model().objects.get(
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


class RelatorioAtasFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    class Meta:
        model = SessaoPlenaria
        fields = ['data_inicio']

    def __init__(self, *args, **kwargs):
        super(RelatorioAtasFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['data_inicio'].label = 'Período (Inicial - Final)'
        self.form.fields['data_inicio'].required = True

        row1 = to_row([('data_inicio', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Atas das Sessões Plenárias'),
                     row1, form_actions(save_label='Pesquisar'))
        )


class RelatorioPresencaSessaoFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    class Meta:
        model = SessaoPlenaria
        fields = ['data_inicio']

    def __init__(self, *args, **kwargs):
        super(RelatorioPresencaSessaoFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['data_inicio'].label = 'Período (Inicial - Final)'
        self.form.fields['data_inicio'].required = True

        row1 = to_row([('data_inicio', 12)])

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Presença dos parlamentares nas sessões plenárias'),
                     row1, form_actions(save_label='Pesquisar'))
        )


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


class ConfiguracoesAppForm(ModelForm):

    class Meta:
        model = AppConfig
        fields = ['documentos_administrativos',
                  'sequencia_numeracao',
                  'painel_aberto',
                  'texto_articulado_proposicao',
                  'texto_articulado_materia',
                  'texto_articulado_norma']
