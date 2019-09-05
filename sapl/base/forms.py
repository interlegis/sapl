import logging
import os

from crispy_forms.bootstrap import FieldWithButtons, InlineRadios, StrictButton
from crispy_forms.layout import HTML, Button, Div, Field, Fieldset, Layout, Row
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.forms import Form, ModelForm
from django.utils import timezone
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
import django_filters

from sapl.audiencia.models import AudienciaPublica, TipoAudienciaPublica
from sapl.audiencia.models import AudienciaPublica, TipoAudienciaPublica
from sapl.base.models import Autor, TipoAutor
from sapl.comissoes.models import Reuniao, Comissao
from sapl.comissoes.models import Reuniao, Comissao
from sapl.crispy_layout_mixin import (SaplFormLayout, form_actions, to_column,
                                      to_row)
from sapl.crispy_layout_mixin import SaplFormHelper
from sapl.materia.models import (MateriaLegislativa, UnidadeTramitacao, StatusTramitacao,
                                 DocumentoAcessorio, TipoMateriaLegislativa)
from sapl.norma.models import (NormaJuridica, NormaEstatisticas)
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.parlamentares.models import SessaoLegislativa, Partido, HistoricoPartido
from sapl.sessao.models import SessaoPlenaria
from sapl.settings import MAX_IMAGE_UPLOAD_SIZE
from sapl.utils import (RANGE_ANOS, YES_NO_CHOICES,
                        ChoiceWithoutValidationField, ImageThumbnailFileInput,
                        RangeWidgetOverride, autor_label, autor_modal,
                        models_with_gr_for_model, qs_override_django_filter,
                        choice_anos_com_normas, choice_anos_com_materias,
                        FilterOverridesMetaMixin, FileFieldCheckMixin,
                        intervalos_tem_intersecao)
from .models import AppConfig, CasaLegislativa
from operator import xor


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


def get_roles():
    roles = [(g.id, g.name) for g in Group.objects.all().order_by('name')
             if g.name != 'Votante']
    return roles


class UsuarioCreateForm(ModelForm):
    logger = logging.getLogger(__name__)
    firstname = forms.CharField(
        required=True,
        label="Nome",
        max_length=30
    )
    lastname = forms.CharField(
        required=True,
        label="Sobrenome",
        max_length=30
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label='Senha',
        min_length=6,
        max_length=128
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label='Confirmar senha',
        min_length=6,
        max_length=128
    )
    user_active = forms.ChoiceField(
        required=True,
        choices=YES_NO_CHOICES,
        label="Usuário ativo?",
        initial='True'
    )
    roles = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple(),
        choices=get_roles
    )

    class Meta:
        model = get_user_model()
        fields = [
            get_user_model().USERNAME_FIELD, 'firstname', 'lastname',
            'password1', 'password2', 'user_active', 'roles'
        ] + (['email']
             if get_user_model().USERNAME_FIELD != 'email' else [])

    def clean(self):
        super().clean()

        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data
        if data['password1'] != data['password2']:
            self.logger.error('Erro de validação. Senhas informadas ({}, {}) são diferentes.'.format(
                data['password1'], data['password2']))
            raise ValidationError('Senhas informadas são diferentes')

        return data

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        row0 = to_row([('username', 12)])

        row1 = to_row([('firstname', 6),
                       ('lastname', 6)])

        row2 = to_row([('email', 6),
                       ('user_active', 6)])
        row3 = to_row(
            [('password1', 6),
             ('password2', 6)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row0,
            row1,
            row3,
            row2,
            'roles',
            form_actions(label='Confirmar'))


class UsuarioFilterSet(django_filters.FilterSet):

    username = django_filters.CharFilter(
        label=_('Nome de Usuário'),
        lookup_expr='icontains')

    class Meta:
        model = User
        fields = ['username']

    def __init__(self, *args, **kwargs):
        super(UsuarioFilterSet, self).__init__(*args, **kwargs)

        row0 = to_row([('username', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Usuário'),
                     row0,
                     form_actions(label='Pesquisar'))
        )


class UsuarioEditForm(ModelForm):
    logger = logging.getLogger(__name__)
    # ROLES = [(g.id, g.name) for g in Group.objects.all().order_by('name')]
    ROLES = []

    password1 = forms.CharField(
        required=False, widget=forms.PasswordInput, label='Senha')
    password2 = forms.CharField(
        required=False, widget=forms.PasswordInput, label='Confirmar senha')
    user_active = forms.ChoiceField(choices=YES_NO_CHOICES, required=True,
                                    label="Usuário ativo?", initial='True')
    roles = forms.MultipleChoiceField(
        required=True, widget=forms.CheckboxSelectMultiple(), choices=get_roles)

    class Meta:
        model = get_user_model()
        fields = [
            get_user_model().USERNAME_FIELD, 'password1',
            'password2', 'user_active', 'roles'
        ] + (['email']
             if get_user_model().USERNAME_FIELD != 'email' else [])

    def __init__(self, *args, **kwargs):

        super(UsuarioEditForm, self).__init__(*args, **kwargs)

        row1 = to_row([('username', 12)])
        row2 = to_row([('email', 6),
                       ('user_active', 6)])
        row3 = to_row(
            [('password1', 6),
             ('password2', 6)])

        row4 = to_row([(form_actions(label='Salvar Alterações'), 6)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row1,
            row2,
            row3,
            'roles',
            form_actions(label='Salvar Alterações'))

    def clean(self):
        super(UsuarioEditForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data
        if data['password1'] and data['password1'] != data['password2']:
            self.logger.error('Erro de validação. Senhas informadas ({}, {}) são diferentes.'.format(
                data['password1'], data['password2']))
            raise ValidationError('Senhas informadas são diferentes')

        return data


class SessaoLegislativaForm(FileFieldCheckMixin, ModelForm):
    logger = logging.getLogger(__name__)

    class Meta:
        model = SessaoLegislativa
        exclude = []

    def clean(self):

        cleaned_data = super(SessaoLegislativaForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        flag_edit = True
        data_inicio = cleaned_data['data_inicio']
        data_fim = cleaned_data['data_fim']
        legislatura = cleaned_data['legislatura']
        numero = cleaned_data['numero']
        data_inicio_leg = legislatura.data_inicio
        data_fim_leg = legislatura.data_fim
        pk = self.initial['id'] if self.initial else None
        # Queries para verificar se existem Sessões Legislativas no período selecionado no form
        # Caso onde a data_inicio e data_fim são iguais a de alguma sessão já
        # criada
        primeiro_caso = Q(data_inicio=data_inicio, data_fim=data_fim)
        # Caso onde a data_inicio está entre o início e o fim de uma Sessão já
        # existente
        segundo_caso = Q(data_inicio__lt=data_inicio,
                         data_fim__range=(data_inicio, data_fim))
        # Caso onde a data_fim está entre o início e o fim de uma Sessão já
        # existente
        terceiro_caso = Q(data_inicio__range=(
            data_inicio, data_fim), data_fim__gt=data_fim)
        sessoes_existentes = SessaoLegislativa.objects.filter(primeiro_caso | segundo_caso | terceiro_caso).\
            exclude(pk=pk)

        if sessoes_existentes:
            raise ValidationError('Já existe registrado uma Sessão Legislativa que coincide com a data '
                                  'inserida, favor verificar as Sessões existentes antes de criar uma '
                                  'nova Sessão Legislativa')

        #sessoes_legislativas = SessaoLegislativa.objects.filter(legislatura=legislatura).exclude(pk=pk)

        # if sessoes_legislativas:
        #     numeracoes = [n.numero for n in sessoes_legislativas]
        #     numeracoes = sorted(numeracoes)
        #     ult = max(numeracoes)
        #
        # else:
        #     ult = SessaoLegislativa.objects.latest('data_fim')
        #     flag_edit = ult.id != pk
        #     ult = ult.numero

        ult = 0

        if numero <= ult and flag_edit:
            self.logger.error('O número da SessaoLegislativa ({}) é menor ou igual '
                              'que o de Sessões Legislativas passadas ({})'.format(numero, ult))
            raise ValidationError('O número da Sessão Legislativa não pode ser menor ou igual '
                                  'que o de Sessões Legislativas passadas')

        if data_inicio < data_inicio_leg or \
                data_inicio > data_fim_leg:
            self.logger.error('A data de início ({}) da SessaoLegislativa está compreendida '
                              'fora da data início ({}) e fim ({}) da Legislatura '
                              'selecionada'.format(data_inicio, data_inicio_leg, data_fim_leg))
            raise ValidationError('A data de início da Sessão Legislativa deve estar compreendida '
                                  'entre a data início e fim da Legislatura selecionada')

        if data_fim > data_fim_leg or \
                data_fim < data_inicio_leg:
            self.logger.error('A data de fim ({}) da SessaoLegislativa está compreendida '
                              'fora da data início ({}) e fim ({}) da Legislatura '
                              'selecionada.'.format(data_fim, data_inicio_leg, data_fim_leg))
            raise ValidationError('A data de fim da Sessão Legislativa deve estar compreendida '
                                  'entre a data início e fim da Legislatura selecionada')

        if data_inicio > data_fim:
            self.logger.error(
                'Data início ({}) superior à data fim ({}).'.format(data_inicio, data_fim))
            raise ValidationError(
                'Data início não pode ser superior à data fim')

        data_inicio_intervalo = cleaned_data['data_inicio_intervalo']
        data_fim_intervalo = cleaned_data['data_fim_intervalo']

        if data_inicio_intervalo and data_fim_intervalo and \
                data_inicio_intervalo > data_fim_intervalo:
            self.logger.error('Data início de intervalo ({}) superior à '
                              'data fim de intervalo ({}).'.format(data_inicio_intervalo, data_fim_intervalo))
            raise ValidationError('Data início de intervalo não pode ser '
                                  'superior à data fim de intervalo')

        if data_inicio_intervalo:
            if data_inicio_intervalo < data_inicio or \
                    data_inicio_intervalo < data_inicio_leg or \
                    data_inicio_intervalo > data_fim or \
                    data_inicio_intervalo > data_fim_leg:
                self.logger.error('A data de início do intervalo ({}) não está compreendida entre '
                                  'as datas de início ({}) e fim ({}) tanto da Legislatura quanto da '
                                  'própria Sessão Legislativa ({} e {}).'
                                  .format(data_inicio_intervalo, data_inicio_leg, data_fim_leg, data_inicio, data_fim))
                raise ValidationError('A data de início do intervalo deve estar compreendida entre '
                                      'as datas de início e fim tanto da Legislatura quanto da '
                                      'própria Sessão Legislativa')
        if data_fim_intervalo:
            if data_fim_intervalo > data_fim or \
                    data_fim_intervalo > data_fim_leg or \
                    data_fim_intervalo < data_inicio or \
                    data_fim_intervalo < data_inicio_leg:
                self.logger.error('A data de fim do intervalo ({}) não está compreendida entre '
                                  'as datas de início ({}) e fim ({}) tanto da Legislatura quanto da '
                                  'própria Sessão Legislativa ({} e {}).'
                                  .format(data_fim_intervalo, data_inicio_leg, data_fim_leg, data_inicio, data_fim))
                raise ValidationError('A data de fim do intervalo deve estar compreendida entre '
                                      'as datas de início e fim tanto da Legislatura quanto da '
                                      'própria Sessão Legislativa')
        return cleaned_data


class TipoAutorForm(ModelForm):

    class Meta:
        model = TipoAutor
        fields = ['descricao']

    def __init__(self, *args, **kwargs):

        super(TipoAutorForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(TipoAutorForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cd = self.cleaned_data
        lista = ['comissão',
                 'comis',
                 'parlamentar',
                 'bancada',
                 'bloco',
                 'comissao',
                 'vereador',
                 'órgão',
                 'orgao',
                 'deputado',
                 'senador',
                 'vereadora',
                 'frente']

        for l in lista:
            if l in cd['descricao'].lower():
                raise ValidationError(_('A descrição colocada não pode ser usada '
                                        'por ser equivalente a um tipo já existente'))


class AutorForm(ModelForm):
    logger = logging.getLogger(__name__)

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
                    _('Filtrar'), css_class='btn-outline-primary btn-filtrar-autor',
                    type='button')),
            css_class='hidden',
            data_action='create',
            data_application='AutorSearch',
            data_field='autor_related')

        autor_select = Row(to_column(('tipo', 3)),
                           Div(to_column(('nome', 7)),
                               to_column(('cargo', 5)),
                               css_class="div_nome_cargo row col"),
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

        self.helper = SaplFormHelper()
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
            self.logger.error(
                'Textos diferentes. ("{}" e "{}")'.format(texto1, texto2))
            raise ValidationError(msg)
        return True

    def clean(self):
        super(AutorForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        User = get_user_model()
        cd = self.cleaned_data

        if 'action_user' not in cd or not cd['action_user']:
            self.logger.error('Não Informado se o Autor terá usuário '
                              'vinculado para acesso ao Sistema.')
            raise ValidationError(_('Informe se o Autor terá usuário '
                                    'vinculado para acesso ao Sistema.'))

        if 'status_user' in self.Meta.fields:
            if self.instance.pk and self.instance.user_id:
                if getattr(
                        self.instance.user,
                        get_user_model().USERNAME_FIELD) != cd['username']:
                    if 'status_user' not in cd or not cd['status_user']:
                        self.logger.error('Foi trocado ou removido o usuário deste Autor ({}), '
                                          'mas não foi informado como se deve proceder '
                                          'com o usuário que está sendo desvinculado? ({})'
                                          .format(cd['username'], get_user_model().USERNAME_FIELD))
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
                self.logger.error(
                    'Não existe usuário com username "%s". ' % cd['username'])
                raise ValidationError(
                    _('Não existe usuário com username "%s". '
                      'Para utilizar esse username você deve selecionar '
                      '"Criar novo Usuário".') % cd['username'])

        if cd['action_user'] != 'N':

            if 'username' not in cd or not cd['username']:
                self.logger.error('Username não informado.')
                raise ValidationError(_('O username deve ser informado.'))

            param_username = {
                'user__' + get_user_model().USERNAME_FIELD: cd['username']}
            if qs_autor.filter(**param_username).exists():
                self.logger.error(
                    'Já existe um Autor para este usuário ({}).'.format(cd['username']))
                raise ValidationError(
                    _('Já existe um usuário vinculado a esse autor'))

        """
        'if' não é necessário por ser campo obrigatório e o framework já
        mostrar a mensagem de obrigatório junto ao campo. mas foi colocado
        ainda assim para renderizar um message.danger no topo do form.
        """
        if 'tipo' not in cd or not cd['tipo']:
            self.logger.error('Tipo do Autor não selecionado.')
            raise ValidationError(
                _('O Tipo do Autor deve ser selecionado.'))

        tipo = cd['tipo']

        if not tipo.content_type:
            if 'nome' not in cd or not cd['nome']:
                self.logger.error('Nome do Autor não informado.')
                raise ValidationError(
                    _('O Nome do Autor deve ser informado.'))
        else:
            if 'autor_related' not in cd or not cd['autor_related']:
                self.logger.error('Registro de %s não escolhido para ser '
                                  'vinculado ao cadastro de Autor' % tipo.descricao)
                raise ValidationError(
                    _('Um registro de %s deve ser escolhido para ser '
                      'vinculado ao cadastro de Autor') % tipo.descricao)

            if not tipo.content_type.model_class().objects.filter(
                    pk=cd['autor_related']).exists():
                self.logger.error('O Registro definido (%s-%s) não está na base '
                                  'de %s.' % (cd['autor_related'], cd['q'], tipo.descricao))
                raise ValidationError(
                    _('O Registro definido (%s-%s) não está na base de %s.'
                      ) % (cd['autor_related'], cd['q'], tipo.descricao))

            qs_autor_selected = qs_autor.filter(
                object_id=cd['autor_related'],
                content_type_id=cd['tipo'].content_type_id)
            if qs_autor_selected.exists():
                autor = qs_autor_selected.first()
                self.logger.error('Já existe um autor Cadastrado para '
                                  '%s' % autor.autor_related)
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


class RelatorioDocumentosAcessoriosFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioDocumentosAcessoriosFilterSet, self).qs
        return parent.distinct().order_by('-data')

    class Meta(FilterOverridesMetaMixin):
        model = DocumentoAcessorio
        fields = ['tipo', 'materia__tipo', 'data']

    def __init__(self, *args, **kwargs):
        
        super(
            RelatorioDocumentosAcessoriosFilterSet, self
        ).__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Documento'
        self.filters['materia__tipo'].label = 'Tipo de Matéria do Documento'
        self.filters['data'].label = 'Período (Data Inicial - Data Final)'
        
        self.form.fields['tipo'].required = True

        row0 = to_row([('tipo', 6),
                       ('materia__tipo', 6)])
    
        row1 = to_row([('data', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa'),
            row0, row1,
            form_actions(label='Pesquisar'))
        )


class RelatorioAtasFilterSet(django_filters.FilterSet):

    class Meta(FilterOverridesMetaMixin):
        model = SessaoPlenaria
        fields = ['data_inicio']

    @property
    def qs(self):
        parent = super(RelatorioAtasFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').exclude(
            upload_ata='').order_by('-data_inicio', 'tipo', 'numero')

    def __init__(self, *args, **kwargs):
        super(RelatorioAtasFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['data_inicio'].label = 'Período (Inicial - Final)'
        self.form.fields['data_inicio'].required = True

        row1 = to_row([('data_inicio', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Atas das Sessões Plenárias'),
                     row1, form_actions(label='Pesquisar'))
        )


def ultimo_ano_com_norma():
    anos_normas = choice_anos_com_normas()

    if anos_normas:
        return anos_normas[0]
    return ''


class RelatorioNormasMesFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Norma',
                                      choices=choice_anos_com_normas,
                                      initial=ultimo_ano_com_norma)

    class Meta:
        model = NormaJuridica
        fields = ['ano']

    def __init__(self, *args, **kwargs):
        super(RelatorioNormasMesFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['ano'].label = 'Ano'
        self.form.fields['ano'].required = True

        row1 = to_row([('ano', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Normas por mês do ano.'),
                     row1, form_actions(label='Pesquisar'))
        )

    @property
    def qs(self):
        parent = super(RelatorioNormasMesFilterSet, self).qs
        return parent.distinct().order_by('data')


class EstatisticasAcessoNormasForm(Form):

    ano = forms.ChoiceField(required=True,
                            label='Ano de acesso',
                            choices=RANGE_ANOS,
                            initial=timezone.now().year)

    class Meta:
        fields = ['ano']

    def __init__(self, *args, **kwargs):
        super(EstatisticasAcessoNormasForm, self).__init__(
            *args, **kwargs)

        row1 = to_row([('ano', 12)])

        self.helper = SaplFormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Fieldset(_('Normas por acessos nos meses do ano.'),
                     row1, form_actions(label='Pesquisar'))
        )

    def clean(self):
        super(EstatisticasAcessoNormasForm, self).clean()

        return self.cleaned_data


class RelatorioNormasVigenciaFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Norma',
                                      choices=choice_anos_com_normas,
                                      initial=ultimo_ano_com_norma)

    vigencia = forms.ChoiceField(
        label=_('Vigência'),
        choices=[(True, "Vigente"), (False, "Não vigente")],
        widget=forms.RadioSelect(),
        required=True,
        initial=True)

    def __init__(self, *args, **kwargs):
        super(RelatorioNormasVigenciaFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['ano'].label = 'Ano'
        self.form.fields['ano'].required = True
        self.form.fields['vigencia'] = self.vigencia

        row1 = to_row([('ano', 12)])
        row2 = to_row([('vigencia', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Normas por vigência.'),
                     row1, row2,
                     form_actions(label='Pesquisar'))
        )

    @property
    def qs(self):
        return qs_override_django_filter(self)


class RelatorioPresencaSessaoFilterSet(django_filters.FilterSet):

    class Meta(FilterOverridesMetaMixin):
        model = SessaoPlenaria
        fields = ['data_inicio',
                  'sessao_legislativa',
                  'tipo',
                  'legislatura']

    def __init__(self, *args, **kwargs):
        super(RelatorioPresencaSessaoFilterSet, self).__init__(
            *args, **kwargs)

        self.form.fields['exibir_ordem_dia'] = forms.BooleanField(required=False, 
                                                                  label='Exibir presença das Ordens do Dia')
        self.form.initial['exibir_ordem_dia']  = True

        self.filters['data_inicio'].label = 'Período (Inicial - Final)'
        
        tipo_sessao_ordinaria = self.filters['tipo'].queryset.filter(nome='Ordinária')
        if tipo_sessao_ordinaria:
            self.form.initial['tipo'] = tipo_sessao_ordinaria.first()

        row1 = to_row([('data_inicio', 12)])
        row2 = to_row([('legislatura', 4),
                       ('sessao_legislativa', 4),
                       ('tipo', 4)])
        row3 = to_row([('exibir_ordem_dia', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Presença dos parlamentares nas sessões plenárias'),
                     row1, row2, row3, form_actions(label='Pesquisar'))
        )

    @property
    def qs(self):
        return qs_override_django_filter(self)


class RelatorioHistoricoTramitacaoFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioHistoricoTramitacaoFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').order_by('-ano', 'tipo', 'numero')

    class Meta(FilterOverridesMetaMixin):
        model = MateriaLegislativa
        fields = ['tipo', 'tramitacao__status', 'tramitacao__data_tramitacao',
                  'tramitacao__unidade_tramitacao_local', 'tramitacao__unidade_tramitacao_destino']

    def __init__(self, *args, **kwargs):
        super(RelatorioHistoricoTramitacaoFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters['tramitacao__status'].label = _('Status')
        self.filters['tramitacao__unidade_tramitacao_local'].label = _(
            'Unidade Local (Origem)')
        self.filters['tramitacao__unidade_tramitacao_destino'].label = _(
            'Unidade Destino')

        row1 = to_row([('tramitacao__data_tramitacao', 12)])
        row2 = to_row([('tramitacao__unidade_tramitacao_local', 6),
                       ('tramitacao__unidade_tramitacao_destino', 6)])
        row3 = to_row(
            [('tipo', 6),
             ('tramitacao__status', 6)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_(''),
                     row1, row2, row3,
                     form_actions(label='Pesquisar'))
        )


class RelatorioDataFimPrazoTramitacaoFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioDataFimPrazoTramitacaoFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').order_by('-ano', 'tipo', 'numero')

    class Meta(FilterOverridesMetaMixin):
        model = MateriaLegislativa
        fields = ['tipo', 'tramitacao__unidade_tramitacao_local',
                  'tramitacao__unidade_tramitacao_destino',
                  'tramitacao__status', 'tramitacao__data_fim_prazo']

    def __init__(self, *args, **kwargs):
        super(RelatorioDataFimPrazoTramitacaoFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters[
            'tramitacao__unidade_tramitacao_local'].label = 'Unidade Local (Origem)'
        self.filters['tramitacao__unidade_tramitacao_destino'].label = 'Unidade Destino'
        self.filters['tramitacao__status'].label = 'Status de tramitação'

        row1 = to_row([('tramitacao__data_fim_prazo', 12)])
        row2 = to_row([('tramitacao__unidade_tramitacao_local', 6),
                       ('tramitacao__unidade_tramitacao_destino', 6)])
        row3 = to_row(
            [('tipo', 6),
             ('tramitacao__status', 6)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Tramitações'),
                     row1, row2, row3,
                     form_actions(label='Pesquisar'))
        )


class RelatorioReuniaoFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioReuniaoFilterSet, self).qs
        return parent.distinct().order_by('-data', 'comissao')

    class Meta:
        model = Reuniao
        fields = ['comissao', 'data',
                  'nome', 'tema']

    def __init__(self, *args, **kwargs):
        super(RelatorioReuniaoFilterSet, self).__init__(
            *args, **kwargs)

        row1 = to_row([('data', 12)])
        row2 = to_row(
            [('comissao', 4),
             ('nome', 4),
             ('tema', 4)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Reunião de Comissão'),
                     row1, row2,
                     form_actions(label='Pesquisar'))
        )


class RelatorioAudienciaFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioAudienciaFilterSet, self).qs
        return parent.distinct().order_by('-data', 'tipo')

    class Meta:
        model = AudienciaPublica
        fields = ['tipo', 'data',
                  'nome']

    def __init__(self, *args, **kwargs):
        super(RelatorioAudienciaFilterSet, self).__init__(
            *args, **kwargs)

        row1 = to_row([('data', 12)])
        row2 = to_row(
            [('tipo', 4),
             ('nome', 4)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Audiência Pública'),
                     row1, row2,
                     form_actions(label='Pesquisar'))
        )


class RelatorioMateriasTramitacaoilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Matéria',
                                      choices=choice_anos_com_materias)

    tramitacao__unidade_tramitacao_destino = django_filters.ModelChoiceFilter(
        queryset=UnidadeTramitacao.objects.all(),
        label=_('Unidade Atual'))

    tramitacao__status = django_filters.ModelChoiceFilter(
        queryset=StatusTramitacao.objects.all(),
        label=_('Status Atual'))

    @property
    def qs(self):
        parent = super(RelatorioMateriasTramitacaoilterSet, self).qs
        return parent.distinct().order_by('-ano', 'tipo', '-numero')

    class Meta:
        model = MateriaLegislativa
        fields = ['ano', 'tipo', 'tramitacao__unidade_tramitacao_destino',
                  'tramitacao__status']

    def __init__(self, *args, **kwargs):
        super(RelatorioMateriasTramitacaoilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'

        row1 = to_row([('ano', 12)])
        row2 = to_row([('tipo', 12)])
        row3 = to_row([('tramitacao__unidade_tramitacao_destino', 12)])
        row4 = to_row([('tramitacao__status', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria em Tramitação'),
                     row1, row2, row3, row4,
                     form_actions(label='Pesquisar'))
        )


class RelatorioMateriasPorAnoAutorTipoFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Matéria',
                                      choices=choice_anos_com_materias)

    class Meta:
        model = MateriaLegislativa
        fields = ['ano']

    def __init__(self, *args, **kwargs):
        super(RelatorioMateriasPorAnoAutorTipoFilterSet, self).__init__(
            *args, **kwargs)

        row1 = to_row(
            [('ano', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1,
                     form_actions(label='Pesquisar'))
        )


class RelatorioMateriasPorAutorFilterSet(django_filters.FilterSet):

    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    @property
    def qs(self):
        parent = super().qs
        return parent.distinct().filter(autoria__primeiro_autor=True)\
            .order_by('autoria__autor', '-autoria__primeiro_autor', 'tipo', '-ano', '-numero')

    class Meta(FilterOverridesMetaMixin):
        model = MateriaLegislativa
        fields = ['tipo', 'data_apresentacao']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1, row2,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row3,
                     form_actions(label='Pesquisar'))
        )


class CasaLegislativaForm(FileFieldCheckMixin, ModelForm):

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
        # chama __clean de FileFieldCheckMixin
        # por estar em clean de campo
        super(CasaLegislativaForm, self)._check()

        logotipo = self.cleaned_data.get('logotipo')
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
    logger = logging.getLogger(__name__)

    mostrar_brasao_painel = forms.BooleanField(
        help_text=_('Sugerimos fortemente que faça o upload de imagens com '
                    'o fundo transparente.'),
        label=_('Mostrar brasão da Casa no painel?'),
        required=False)

    class Meta:
        model = AppConfig
        fields = ['documentos_administrativos',
                  'sequencia_numeracao_protocolo',
                  'sequencia_numeracao_proposicao',
                  'esfera_federacao',
                  # 'painel_aberto', # TODO: a ser implementado na versão 3.2
                  'texto_articulado_proposicao',
                  'texto_articulado_materia',
                  'texto_articulado_norma',
                  'proposicao_incorporacao_obrigatoria',
                  'protocolo_manual',
                  'mostrar_brasao_painel',
                  'receber_recibo_proposicao',
                  'assinatura_ata',
                  'estatisticas_acesso_normas',
                  'escolher_numero_materia_proposicao',
                  'tramitacao_materia',
                  'tramitacao_documento']

    def clean_mostrar_brasao_painel(self):
        mostrar_brasao_painel = self.cleaned_data.get(
            'mostrar_brasao_painel', False)
        casa = CasaLegislativa.objects.first()

        if not casa:
            self.logger.error('Não há casa legislativa relacionada.')
            raise ValidationError("Não há casa legislativa relacionada.")

        if not casa.logotipo and mostrar_brasao_painel:
            self.logger.error('Não há logitipo configurado para esta '
                              'CasaLegislativa ({}).'.format(casa))
            raise ValidationError("Não há logitipo configurado para esta "
                                  "Casa legislativa.")

        return mostrar_brasao_painel


class RecuperarSenhaForm(PasswordResetForm):

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        row1 = to_row(
            [('email', 12)])
        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Insira o e-mail cadastrado com a sua conta'),
                     row1,
                     form_actions(label='Enviar'))
        )

        super(RecuperarSenhaForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(RecuperarSenhaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        email_existente = User.objects.filter(
            email=self.data['email']).exists()

        if not email_existente:
            msg = 'Não existe nenhum usuário cadastrado com este e-mail.'
            self.logger.error('Não existe nenhum usuário cadastrado com este e-mail ({}).'
                              .format(self.data['email']))
            raise ValidationError(msg)

        return self.cleaned_data


class NovaSenhaForm(SetPasswordForm):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(NovaSenhaForm, self).__init__(user, *args, **kwargs)

        row1 = to_row(
            [('new_password1', 6),
             ('new_password2', 6)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row1,
            form_actions(label='Enviar'))


class AlterarSenhaForm(Form):
    logger = logging.getLogger(__name__)

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

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row1,
            row2,
            form_actions(label='Alterar Senha'))

    def clean(self):
        super(AlterarSenhaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data

        new_password1 = data['new_password1']
        new_password2 = data['new_password2']

        if new_password1 != new_password2:
            self.logger.error("'Nova Senha' ({}) diferente de 'Confirmar Senha' ({})".format(
                new_password1, new_password2))
            raise ValidationError(
                "'Nova Senha' diferente de 'Confirmar Senha'")

        # TODO: colocar mais regras como: tamanho mínimo,
        # TODO: caracteres alfanuméricos, maiúsculas (?),
        # TODO: senha atual igual a senha anterior, etc

        if len(new_password1) < 6:
            self.logger.error(
                'A senha informada ({}) não tem o mínimo de 6 caracteres.'.format(new_password1))
            raise ValidationError(
                "A senha informada deve ter no mínimo 6 caracteres")

        username = data['username']
        old_password = data['old_password']
        user = User.objects.get(username=username)

        if user.is_anonymous():
            self.logger.error(
                'Não é possível alterar senha de usuário anônimo ({}).'.format(username))
            raise ValidationError(
                "Não é possível alterar senha de usuário anônimo")

        if not user.check_password(old_password):
            self.logger.error('Senha atual informada ({}) não confere '
                              'com a senha armazenada.'.format(old_password))
            raise ValidationError("Senha atual informada não confere "
                                  "com a senha armazenada")

        if user.check_password(new_password1):
            self.logger.error(
                'Nova senha ({}) igual à senha anterior.'.format(new_password1))
            raise ValidationError(
                "Nova senha não pode ser igual à senha anterior")

        return self.cleaned_data


class PartidoForm(FileFieldCheckMixin, ModelForm):

    class Meta:
        model = Partido
        exclude = []

    def __init__(self, *args, **kwargs):

        super(PartidoForm, self).__init__(*args, **kwargs)

        # TODO Utilizar esses campos na issue #2161 de alteração de nomes de partidos
        # if self.instance:
        #     if self.instance.nome:
        #         self.fields['nome'].widget.attrs['readonly'] = True
        #         self.fields['sigla'].widget.attrs['readonly'] = True

        row1 = to_row(
            [('sigla', 2),
             ('nome', 6),
             ('data_criacao', 2),
             ('data_extincao', 2), ])
        row2 = to_row([('observacao', 12)])
        row3 = to_row([('logo_partido', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row1, row2, row3,
            form_actions(label='Salvar')
        )

    def clean(self):
        super(PartidoForm,self).clean()
        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return cleaned_data

        if cleaned_data['data_criacao'] and cleaned_data['data_extincao'] and cleaned_data['data_criacao'] > \
                cleaned_data['data_extincao']:
            raise ValidationError("Certifique-se de que a data de criação seja anterior à data de extinção.")

        if self.instance.pk:
            partido = Partido.objects.get(pk=self.instance.pk)

            if xor(cleaned_data['sigla'] == partido.sigla, cleaned_data['nome'] == partido.nome):
                raise ValidationError(_('O Partido deve ter um novo nome e uma nova sigla.'))

            cleaned_data.update({'partido': partido})

        return cleaned_data

class PartidoUpdateForm(PartidoForm):

    opcoes = YES_NO_CHOICES

    historico = forms.ChoiceField(initial=False, choices=opcoes)


    class Meta:
        model = Partido
        exclude = []


    def __init__(self, pk=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row1 = to_row([
            ('sigla', 6),
            ('nome', 6),
            ]
        )
        row2 = to_row([
            ('historico', 2),
            ('data_criacao', 5),
            ('data_extincao', 5),
            ]
        )
        row3 = to_row([('observacao', 12)])
        row4 = to_row([('logo_partido', 12)])

        buttons = FormActions(
           *[
               HTML('''<a href="/sistema/parlamentar/partido/{{object.id}}" class="btn btn-dark btn-close-container">%s</a>''' % _('Cancelar'))
           ],
            Submit('salvar', _('Salvar'), css_class='float-right',
               onclick='return true;'),
            css_class='form-group row justify-content-between'
        )

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            row1, row2, row3, row4, to_row([(buttons, 12)]),
        )




    def clean(self):
        cleaned_data = super(PartidoUpdateForm,self).clean()
        
        if not self.is_valid():
            return cleaned_data

        if cleaned_data['data_criacao'] and cleaned_data['data_extincao']:
            if cleaned_data['data_criacao'] > cleaned_data['data_extincao']:
                raise ValidationError(
                    "Certifique-se de que a data de criação seja anterior à data de extinção.")

        return cleaned_data

    def save(self,commit=False):
        partido = self.instance
    
        cleaned_data = self.cleaned_data
        is_historico = cleaned_data['historico'] == 'True'
            
        if not is_historico:
            partido.save(commit)
        else:
            sigla = self.cleaned_data['sigla']
            nome = self.cleaned_data['nome']
            inicio_historico = self.cleaned_data['data_criacao']
            fim_historico = self.cleaned_data['data_extincao']
            logo_partido = self.cleaned_data['logo_partido']
            historico_partido = HistoricoPartido(sigla=sigla,
                                                nome=nome,
                                                inicio_historico=inicio_historico,
                                                fim_historico=fim_historico,
                                                logo_partido=logo_partido,
                                                partido=partido,
                                                )
            historico_partido.save()
        return partido

class RelatorioHistoricoTramitacaoAdmFilterSet(django_filters.FilterSet):

    @property
    def qs(self):
        parent = super(RelatorioHistoricoTramitacaoAdmFilterSet, self).qs
        return parent.distinct().prefetch_related('tipo').order_by('-ano', 'tipo', 'numero')

    class Meta(FilterOverridesMetaMixin):
        model = DocumentoAdministrativo
        fields = ['tipo', 'tramitacaoadministrativo__status',
                  'tramitacaoadministrativo__data_tramitacao',
                  'tramitacaoadministrativo__unidade_tramitacao_local',
                  'tramitacaoadministrativo__unidade_tramitacao_destino']

    def __init__(self, *args, **kwargs):
        super(RelatorioHistoricoTramitacaoAdmFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Documento'
        self.filters['tramitacaoadministrativo__status'].label = _('Status')
        self.filters['tramitacaoadministrativo__unidade_tramitacao_local'].label = _(
            'Unidade Local (Origem)')
        self.filters['tramitacaoadministrativo__unidade_tramitacao_destino'].label = _(
            'Unidade Destino')

        row1 = to_row([('tramitacaoadministrativo__data_tramitacao', 12)])
        row2 = to_row([('tramitacaoadministrativo__unidade_tramitacao_local', 6),
                       ('tramitacaoadministrativo__unidade_tramitacao_destino', 6)])
        row3 = to_row(
            [('tipo', 6),
             ('tramitacaoadministrativo__status', 6)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_(''),
                     row1, row2, row3,
                     form_actions(label='Pesquisar'))
        )


class RelatorioNormasPorAutorFilterSet(django_filters.FilterSet):

    autorianorma__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    @property
    def qs(self):
        parent = super().qs
        return parent.distinct().filter(autorianorma__primeiro_autor=True)\
            .order_by('autorianorma__autor', '-autorianorma__primeiro_autor', 'tipo', '-ano', '-numero')

    class Meta(FilterOverridesMetaMixin):
        model = NormaJuridica
        fields = ['tipo', 'data']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Norma'

        row1 = to_row(
            [('tipo', 12)])
        row2 = to_row(
            [('data', 12)])
        row3 = to_row(
            [('autorianorma__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'Limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1, row2,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row3,
                     form_actions(label='Pesquisar'))
        )
