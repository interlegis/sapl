from crispy_forms.bootstrap import FieldWithButtons, InlineRadios, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Div, Field, Fieldset, Layout, Row
from crispy_forms.templatetags.crispy_forms_field import css_class
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.contrib.contenttypes.fields import GenericRel
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _, string_concat
import django_filters

from sapl.base.models import Autor, TipoAutor
from sapl.crispy_layout_mixin import (SaplFormLayout, form_actions, to_column,
                                      to_row)
from sapl.materia.models import MateriaLegislativa
from sapl.sessao.models import SessaoPlenaria
from sapl.settings import MAX_IMAGE_UPLOAD_SIZE
from sapl.utils import (RANGE_ANOS, ImageThumbnailFileInput,
                        RangeWidgetOverride, autor_label, autor_modal)

from .models import AppConfig, CasaLegislativa


ACTION_CREATE_USERS_AUTOR_CHOICE = [
    ('C', _('Criar novo Usuário')),
    ('A', _('Associar um usuário existente')),
    ('N', _('Autor sem Usuário de Acesso ao Sapl')),
]


STATUS_USER_CHOICE = [
    ('R', _('Apenas retirar Perfil de Autor do Usuário que está sendo'
            ' desvinculado')),
    ('D', _('Retirar Perfil de Autor e desativar Usuário que está sendo'
            ' desvinculado')),
    ('X', _('Excluir Usuário')),
]


class TipoAutorForm(ModelForm):

    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        label=TipoAutor._meta.get_field('content_type').verbose_name,
        required=False)

    class Meta:
        model = TipoAutor
        fields = ['descricao',
                  'content_type']

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


class ChoiceWithoutValidationField(forms.ChoiceField):

    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'], code='required')


class AutorForm(ModelForm):
    senha = forms.CharField(
        max_length=20,
        label=_('Senha'),
        required=False,
        widget=forms.PasswordInput())

    senha_confirma = forms.CharField(
        max_length=20,
        label=_('Confirmar Senha'),
        required=False,
        widget=forms.PasswordInput())

    email = forms.EmailField(
        required=False,
        label=_('Email'))

    confirma_email = forms.EmailField(
        required=False,
        label=_('Confirmar Email'))

    username = forms.CharField(label=get_user_model()._meta.get_field(
        'username').verbose_name.capitalize(),
        required=False,
        max_length=50)

    q = forms.CharField(
        max_length=50, required=False,
        label='Pesquise o nome do Autor com o '
        'tipo Selecionado e marque o escolhido.')

    autor_related = ChoiceWithoutValidationField(label='',
                                                 required=False,
                                                 widget=forms.RadioSelect())

    action_user = forms.ChoiceField(
        label=_('Usuário com acesso ao Sistema para este Autor'),
        choices=ACTION_CREATE_USERS_AUTOR_CHOICE,
        widget=forms.RadioSelect())

    status_user = forms.ChoiceField(
        label=_('Bloqueio do Usuário Existente'),
        choices=STATUS_USER_CHOICE,
        widget=forms.RadioSelect(),
        required=False,
        help_text=_('Se vc está trocando ou removendo o usuário deste Autor, '
                    'como o Sistema deve proceder com o usuário que está sendo'
                    ' desvinculado?'))

    class Meta:
        model = Autor
        fields = ['tipo',
                  'nome',
                  'cargo',
                  'autor_related',
                  'q',
                  'action_user',
                  'username']

    def __init__(self, *args, **kwargs):

        autor_related = Div(
            FieldWithButtons(
                Field('q',
                      placeholder=_('Pesquisar por possíveis autores para '
                                    'o Tipo de Autor selecionado.')),
                StrictButton(
                    _('Filtrar'), css_class='btn-default btn-filtrar-autor',
                    type='button')),


            css_class='hidden',
            data_action='create',
            data_application='AutorSearch',
            data_field='autor_related')

        autor_select = Row(to_column(('tipo', 3)),
                           Div(to_column(('nome', 5)),
                               to_column(('cargo', 4)), css_class="div_nome_cargo"),
                           to_column((autor_related, 9)),
                           to_column((Div(
                               Field('autor_related'),
                               css_class='radiogroup-autor-related hidden'),
                               12)))

        row2 = Row(to_column((InlineRadios('action_user'), 8)),
                   to_column((Div('username'), 4)))
        row3 = Row(to_column(('senha', 3)),
                   to_column(('senha_confirma', 3)),
                   to_column(('email', 3)),
                   to_column(('confirma_email', 3)),
                   css_class='new_user_fields hidden')

        row4 = Row(to_column((Div(InlineRadios('status_user'),
                                  css_class='radiogroup-status hidden'), 12)))

        controle_acesso = Fieldset(
            _('Controle de Acesso do Autor'),
            row2, row3, row4
        )

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(autor_select, controle_acesso)

        super(AutorForm, self).__init__(*args, **kwargs)

        self.fields['action_user'].initial = 'N'

        if self.instance.pk:
            if self.instance.autor_related:
                self.fields['autor_related'].choices = [
                    (self.instance.autor_related.pk,
                     self.instance.autor_related)]
                self.fields['q'].initial = self.instance.nome

            if self.instance.user:
                self.fields['username'].initial = self.instance.user.username
                self.fields['action_user'].initial = 'A'
                self.fields['status_user'].initial = 'R'
                self.fields['username'].label = string_concat(
                    self.fields['username'].label,
                    ' (', self.instance.user.username, ')')
                self.fields['status_user'].label = string_concat(
                    self.fields['status_user'].label,
                    ' (', self.instance.user.username, ')')
            self.fields['username'].widget.attrs.update({
                'data': self.instance.user.username
                if self.instance.user else ''})

            self.fields['status_user'].widget.attrs.update({
                'data': self.instance.user.username
                if self.instance.user else ''})

    def valida_igualdade(self, texto1, texto2, msg):
        if texto1 != texto2:
            raise ValidationError(msg)
        return True

    def clean(self):
        User = get_user_model()
        cd = self.cleaned_data

        if 'action_user' not in cd or not cd['action_user']:
            raise ValidationError(_('Informe se o Autor terá usuário '
                                    'vinculado para acesso ao Sistema.'))

        if self.instance.pk and self.instance.user_id:
            if self.instance.user.username != cd['username']:
                if 'status_user' not in cd or not cd['status_user']:
                    raise ValidationError(
                        _('Foi trocado ou removido o usuário deste Autor, '
                          'mas não foi informado como se deve proceder com o '
                          'usuário que está sendo desvinculado?'))

        qs_user = User.objects.all()
        qs_autor = Autor.objects.all()

        if self.instance.pk:
            qs_autor = qs_autor.exclude(pk=self.instance.pk)
            if self.instance.user:
                qs_user = qs_user.exclude(pk=self.instance.user.pk)

        if cd['action_user'] == 'C':
            if User.objects.filter(username=cd['username']).exists():
                raise ValidationError(
                    _('Já existe usuário com o username "%s". '
                      'Para utilizar esse username você deve selecionar '
                      '"Associar um usuário existente".') % cd['username'])

            if ('senha' not in cd or 'senha_confirma' not in cd or
                    not cd['senha'] or not cd['senha_confirma']):
                raise ValidationError(_(
                    'A senha e sua confirmação devem ser informadas.'))
            msg = _('As senhas não conferem.')
            self.valida_igualdade(cd['senha'], cd['senha_confirma'], msg)

            try:
                validate_password(self.cleaned_data['senha'])
            except ValidationError as error:
                raise ValidationError(error)

            if ('email' not in cd or 'confirma_email' not in cd or
                    not cd['email'] or not cd['confirma_email']):
                raise ValidationError(_(
                    'O email e sua confirmação devem ser informados.'))
            msg = _('Os emails não conferem.')
            self.valida_igualdade(cd['email'], cd['confirma_email'], msg)

            if qs_user.filter(email=cd['email']).exists():
                raise ValidationError(_('Este email já foi cadastrado.'))

            if qs_autor.filter(user__email=cd['email']).exists():
                raise ValidationError(
                    _('Já existe um Autor com este email.'))

        elif cd['action_user'] == 'A':
            if not User.objects.filter(username=cd['username']).exists():
                raise ValidationError(
                    _('Não existe usuário com username "%s". '
                      'Para utilizar esse username você deve selecionar '
                      '"Criar novo Usuário".') % cd['username'])

        if cd['action_user'] != 'N':

            if 'username' not in cd or not cd['username']:
                raise ValidationError(_('O username deve ser informado.'))

            if qs_autor.filter(user__username=cd['username']).exists():
                raise ValidationError(
                    _('Já existe um Autor para este usuário.'))

        """
        'if' não é necessário por ser campo obrigatório e o framework já
        mostrar a mensagem de obrigatório junto ao campo. mas foi colocado
        ainda assim para renderizar um message.danger no topo do form.
        """
        if 'tipo' not in cd or not cd['tipo']:
            raise ValidationError(
                _('O Tipo do Autor deve ser selecionado.'))

        tipo = cd['tipo']

        if not tipo.content_type:
            if 'nome' not in cd or not cd['nome']:
                raise ValidationError(
                    _('O Nome do Autor deve ser informado.'))
        else:
            if 'autor_related' not in cd or not cd['autor_related']:
                raise ValidationError(
                    _('Um registro de %s deve ser escolhido para ser '
                      'vinculado ao cadastro de Autor') % tipo.descricao)

            if not tipo.content_type.model_class().objects.filter(
                    pk=cd['autor_related']).exists():
                raise ValidationError(
                    _('O Registro definido (%s-%s) não está na base de %s.'
                      ) % (cd['autor_related'], cd['q'], tipo.descricao))

            if qs_autor.filter(object_id=cd['autor_related']).exists():
                autor = qs_autor.filter(object_id=cd['autor_related']).first()
                raise ValidationError(
                    _('Já existe um autor Cadastrado para %s'
                      ) % autor.autor_related)

        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=False):
        autor = super(AutorForm, self).save(commit)

        user_old = autor.user if autor.user_id else None

        u = None
        if self.cleaned_data['action_user'] == 'A':
            u = get_user_model().objects.get(
                username=self.cleaned_data['username'])
        elif self.cleaned_data['action_user'] == 'C':
            u = get_user_model().objects.create(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'])
            u.set_password(self.cleaned_data['senha'])
            # Define usuário como ativo em ambiente de desenvolvimento
            # pode logar sem a necessidade de passar pela validação de email
            # troque par False para testar o envio de email em desenvolvimento
            u.is_active = settings.DEBUG
            u.save()
        autor.user = u

        if not autor.tipo.content_type:
            autor.content_type = None
            autor.object_id = None
            autor.autor_related = None
        else:
            autor.autor_related = autor.tipo.content_type.model_class(
            ).objects.get(pk=self.cleaned_data['autor_related'])
            autor.nome = str(autor.autor_related)

        autor.save()

        # FIXME melhorar captura de grupo de Autor, levando em conta,
        # no mínimo, a tradução.
        grupo = Group.objects.filter(name='Autor')[0]
        if self.cleaned_data['action_user'] != 'N':
            autor.user.groups.add(grupo)
            if user_old and user_old != autor.user:
                user_old.groups.remove(grupo)

        else:
            if 'status_user' in self.cleaned_data and user_old:
                if self.cleaned_data['status_user'] == 'X':
                    user_old.delete()

                elif self.cleaned_data['status_user'] == 'D':
                    user_old.groups.remove(grupo)
                    user_old.is_active = False
                    user_old.save()

                elif self.cleaned_data['status_user'] == 'R':
                    user_old.groups.remove(grupo)
            elif user_old:
                user_old.groups.remove(grupo)

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
