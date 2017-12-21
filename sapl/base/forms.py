from crispy_forms.bootstrap import FieldWithButtons, InlineRadios, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Div, Field, Fieldset, Layout, Row
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.forms import ModelForm, Form
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _

import django_filters

from sapl.base.models import Autor, TipoAutor
from sapl.crispy_layout_mixin import (SaplFormLayout, form_actions, to_column,
                                      to_row)
from sapl.materia.models import MateriaLegislativa
from sapl.sessao.models import SessaoPlenaria
from sapl.settings import MAX_IMAGE_UPLOAD_SIZE
from sapl.utils import (RANGE_ANOS, ChoiceWithoutValidationField,
                        ImageThumbnailFileInput, RangeWidgetOverride,
                        autor_label, autor_modal, models_with_gr_for_model,
                        qs_override_django_filter)

from .models import AppConfig, CasaLegislativa


ACTION_CREATE_USERS_AUTOR_CHOICE = [
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

    class Meta:
        model = TipoAutor
        fields = ['descricao']

    def __init__(self, *args, **kwargs):

        super(TipoAutorForm, self).__init__(*args, **kwargs)


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
        get_user_model().USERNAME_FIELD).verbose_name.capitalize(),
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
                               to_column(('cargo', 4)),
                               css_class="div_nome_cargo"),
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

        row4 = Row(to_column((
            Div(InlineRadios('status_user'),
                css_class='radiogroup-status hidden'),
            12))) if 'status_user' in self.Meta.fields else None

        controle_acesso = [row2, row3]

        if row4:
            controle_acesso.append(row4)
        controle_acesso = Fieldset(_('Controle de Acesso do Autor'),
                                   *controle_acesso)

        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(autor_select, controle_acesso)

        super(AutorForm, self).__init__(*args, **kwargs)

        self.fields['action_user'].initial = 'N'

        if self.instance.pk:
            if self.instance.autor_related:
                self.fields['autor_related'].choices = [
                    (self.instance.autor_related.pk,
                     self.instance.autor_related)]

                self.fields['q'].initial = ''

            self.fields['autor_related'].initial = self.instance.autor_related

            if self.instance.user:
                self.fields['username'].initial = getattr(
                    self.instance.user,
                    get_user_model().USERNAME_FIELD)
                self.fields['action_user'].initial = 'A'

                self.fields['username'].label = string_concat(
                    self.fields['username'].label,
                    ' (', getattr(
                        self.instance.user,
                        get_user_model().USERNAME_FIELD), ')')

                if 'status_user' in self.Meta.fields:
                    self.fields['status_user'].initial = 'R'
                    self.fields['status_user'].label = string_concat(
                        self.fields['status_user'].label,
                        ' (', getattr(
                            self.instance.user,
                            get_user_model().USERNAME_FIELD), ')')

            self.fields['username'].widget.attrs.update({
                'data': getattr(
                    self.instance.user,
                    get_user_model().USERNAME_FIELD)
                if self.instance.user else ''})

            if 'status_user' in self.Meta.fields:
                self.fields['status_user'].widget.attrs.update({
                    'data': getattr(
                        self.instance.user,
                        get_user_model().USERNAME_FIELD)
                    if self.instance.user else ''})

    def valida_igualdade(self, texto1, texto2, msg):
        if texto1 != texto2:
            raise ValidationError(msg)
        return True

    def clean(self):
        super(AutorForm, self).clean()

        User = get_user_model()
        cd = self.cleaned_data

        if 'action_user' not in cd or not cd['action_user']:
            raise ValidationError(_('Informe se o Autor terá usuário '
                                    'vinculado para acesso ao Sistema.'))

        if 'status_user' in self.Meta.fields:
            if self.instance.pk and self.instance.user_id:
                if getattr(
                        self.instance.user,
                        get_user_model().USERNAME_FIELD) != cd['username']:
                    if 'status_user' not in cd or not cd['status_user']:
                        raise ValidationError(
                            _('Foi trocado ou removido o usuário deste Autor, '
                              'mas não foi informado como se deve proceder '
                              'com o usuário que está sendo desvinculado?'))

        qs_user = User.objects.all()
        qs_autor = Autor.objects.all()

        if self.instance.pk:
            qs_autor = qs_autor.exclude(pk=self.instance.pk)
            if self.instance.user:
                qs_user = qs_user.exclude(pk=self.instance.user.pk)

        if cd['action_user'] == 'A':
            param_username = {get_user_model().USERNAME_FIELD: cd['username']}
            if not User.objects.filter(**param_username).exists():
                raise ValidationError(
                    _('Não existe usuário com username "%s". '
                      'Para utilizar esse username você deve selecionar '
                      '"Criar novo Usuário".') % cd['username'])

        if cd['action_user'] != 'N':

            if 'username' not in cd or not cd['username']:
                raise ValidationError(_('O username deve ser informado.'))

            param_username = {
                'user__' + get_user_model().USERNAME_FIELD: cd['username']}
            if qs_autor.filter(**param_username).exists():
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

            qs_autor_selected = qs_autor.filter(
                object_id=cd['autor_related'],
                content_type_id=cd['tipo'].content_type_id)
            if qs_autor_selected.exists():
                autor = qs_autor_selected.first()
                raise ValidationError(
                    _('Já existe um autor Cadastrado para %s'
                      ) % autor.autor_related)

        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=False):
        autor = super(AutorForm, self).save(commit)

        user_old = autor.user if autor.user_id else None

        u = None
        param_username = {
            get_user_model().USERNAME_FIELD: self.cleaned_data['username']}
        if self.cleaned_data['action_user'] == 'A':
            u = get_user_model().objects.get(**param_username)
            if not u.is_active:
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
            if 'status_user' in self.Meta.fields:
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
            elif user_old:
                user_old.groups.remove(grupo)

        return autor


class AutorFormForAdmin(AutorForm):
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
                  'username',
                  'status_user']


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
                     row1, form_actions(label='Pesquisar'))
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
                     row1, form_actions(label='Pesquisar'))
        )

    @property
    def qs(self):
        return qs_override_django_filter(self)


class RelatorioHistoricoTramitacaoFilterSet(django_filters.FilterSet):

    filter_overrides = {models.DateField: {
        'filter_class': django_filters.DateFromToRangeFilter,
        'extra': lambda f: {
            'label': '%s (%s)' % (f.verbose_name, _('Inicial - Final')),
            'widget': RangeWidgetOverride}
    }}

    @property
    def qs(self):
        parent = super(RelatorioHistoricoTramitacaoFilterSet, self).qs
        return parent.distinct().order_by('-ano', 'tipo', 'numero')

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
                     form_actions(label='Pesquisar'))
        )


class RelatorioMateriasTramitacaoilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Matéria',
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
                     form_actions(label='Pesquisar'))
        )


class RelatorioMateriasPorAnoAutorTipoFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Matéria',
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
                     form_actions(label='Pesquisar'))
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
                     form_actions(label='Pesquisar'))
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
                raise ValidationError("Imagem muito grande. ( > 2MB )")
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

    mostrar_brasao_painel = forms.BooleanField(
        help_text=_('Sugerimos fortemente que faça o upload de imagens com '
                    'o fundo transparente.'),
        label=_('Mostrar brasão da Casa no painel?'),
        required=False)

    class Meta:
        model = AppConfig
        fields = ['documentos_administrativos',
                  'sequencia_numeracao',
                  # 'painel_aberto', # TODO: a ser implementado na versão 3.2
                  'texto_articulado_proposicao',
                  'texto_articulado_materia',
                  'texto_articulado_norma',
                  'proposicao_incorporacao_obrigatoria',
                  'cronometro_discurso',
                  'cronometro_aparte',
                  'cronometro_ordem',
                  'mostrar_brasao_painel']

    def __init__(self, *args, **kwargs):
        super(ConfiguracoesAppForm, self).__init__(*args, **kwargs)
        self.fields['cronometro_discurso'].widget.attrs['class'] = 'cronometro'
        self.fields['cronometro_aparte'].widget.attrs['class'] = 'cronometro'
        self.fields['cronometro_ordem'].widget.attrs['class'] = 'cronometro'

    def clean_mostrar_brasao_painel(self):
        mostrar_brasao_painel = self.cleaned_data.get(
            'mostrar_brasao_painel', False)
        casa = CasaLegislativa.objects.first()

        if not casa:
            raise ValidationError("Não há casa legislativa relacionada")

        if (not bool(casa.logotipo) and mostrar_brasao_painel):
            raise ValidationError("Não há logitipo configurado para esta "
                                  "Casa legislativa.")

        return mostrar_brasao_painel


class RecuperarSenhaForm(PasswordResetForm):

    def __init__(self, *args, **kwargs):
        row1 = to_row(
            [('email', 12)])
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Insira o e-mail cadastrado com a sua conta'),
                     row1,
                     form_actions(label='Enviar'))
        )

        super(RecuperarSenhaForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(RecuperarSenhaForm, self).clean()

        email_existente = User.objects.filter(
            email=self.data['email']).exists()

        if not email_existente:
            msg = 'Não existe nenhum usuário cadastrado com este e-mail.'
            raise ValidationError(msg)

        return self.cleaned_data


class NovaSenhaForm(SetPasswordForm):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(NovaSenhaForm, self).__init__(user, *args, **kwargs)

        row1 = to_row(
            [('new_password1', 6),
             ('new_password2', 6)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            row1,
            form_actions(label='Enviar'))


class AlterarSenhaForm(Form):

    username = forms.CharField(widget=forms.HiddenInput())

    old_password = forms.CharField(label='Senha atual',
                                   max_length=50,
                                   widget=forms.PasswordInput())
    new_password1 = forms.CharField(label='Nova senha',
                                    max_length=50,
                                    widget=forms.PasswordInput())
    new_password2 = forms.CharField(label='Confirmar senha',
                                    max_length=50,
                                    widget=forms.PasswordInput())


    class Meta:
        fields = ['username', 'old_password', 'new_password1', 'new_password2']

    def __init__(self, *args, **kwargs):

        super(AlterarSenhaForm, self).__init__(*args, **kwargs)

        row1 = to_row([('old_password', 12)])
        row2 = to_row(
            [('new_password1', 6),
             ('new_password2', 6)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            row1,
            row2,
            form_actions(label='Alterar Senha'))

    def clean(self):
        super(AlterarSenhaForm, self).clean()

        data = self.cleaned_data

        new_password1 = data['new_password1']
        new_password2 = data['new_password2']

        if new_password1 != new_password2:
            raise ValidationError("'Nova Senha' diferente de 'Confirmar Senha'")

        # TODO: colocar mais regras como: tamanho mínimo,
        # TODO: caracteres alfanuméricos, maiúsculas (?),
        # TODO: senha atual igual a senha anterior, etc

        if len(new_password1) < 6:
            raise ValidationError("A senha informada deve ter no mínimo 6 caracteres")

        username = data['username']
        old_password = data['old_password']
        user = User.objects.get(username=username)

        if user.is_anonymous():
            raise ValidationError("Não é possível alterar senha de usuário anônimo")

        if not user.check_password(old_password):
            raise ValidationError("Senha atual informada não confere "
                                  "com a senha armazenada")

        if user.check_password(new_password1):
            raise ValidationError("Nova senha não pode ser igual à senha anterior")

        return self.cleaned_data