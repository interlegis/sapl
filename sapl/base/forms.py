import logging
import os

from crispy_forms.bootstrap import FieldWithButtons, InlineRadios, StrictButton, FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Div, Field, Fieldset, Layout, Row, Submit
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.auth.models import Group, User, Permission
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.forms import Form, ModelForm
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from haystack.forms import ModelSearchForm
import django_filters

from sapl.audiencia.models import AudienciaPublica
from sapl.base.models import Autor, TipoAutor, OperadorAutor
from sapl.comissoes.models import Reuniao
from sapl.crispy_layout_mixin import (form_actions, to_column, to_row,
                                      SaplFormHelper, SaplFormLayout)
from sapl.materia.models import (DocumentoAcessorio, MateriaEmTramitacao,
                                 MateriaLegislativa, UnidadeTramitacao,
                                 StatusTramitacao)
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Partido, SessaoLegislativa,\
    Parlamentar, Votante
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.rules import SAPL_GROUP_AUTOR, SAPL_GROUP_VOTANTE
from sapl.sessao.models import SessaoPlenaria
from sapl.settings import MAX_IMAGE_UPLOAD_SIZE
from sapl.utils import (autor_label, autor_modal, ChoiceWithoutValidationField,
                        choice_anos_com_normas, choice_anos_com_materias,
                        FilterOverridesMetaMixin, FileFieldCheckMixin,
                        ImageThumbnailFileInput, qs_override_django_filter,
                        RANGE_ANOS, YES_NO_CHOICES, choice_tipos_normas,
                        GoogleRecapthaMixin, parlamentares_ativos)

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


class UserAdminForm(ModelForm):

    is_active = forms.TypedChoiceField(label=_('Usuário Ativo'),
                                       choices=YES_NO_CHOICES,
                                       coerce=lambda x: x == 'True')

    new_password1 = forms.CharField(
        label='Nova senha',
        max_length=50,
        strip=False,
        required=False,
        widget=forms.PasswordInput(),
        help_text='Deixe os campos em branco para não fazer alteração de senha')

    new_password2 = forms.CharField(
        label='Confirmar senha',
        max_length=50,
        strip=False,
        required=False,
        widget=forms.PasswordInput(),
        help_text='Deixe os campos em branco para não fazer alteração de senha')

    token = forms.CharField(
        required=False,
        label="Token",
        max_length=40,
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    parlamentar = forms.ModelChoiceField(
        label=_('Este usuário é um Parlamentar Votante?'),
        queryset=Parlamentar.objects.all(),
        required=False,
        help_text='Se o usuário que está sendo cadastrado (ou em edição) é um usuário para que um parlamentar possa votar, você pode selecionar o parlamentar nas opções acima.')

    autor = forms.ModelChoiceField(
        label=_('Este usuário registrará proposições para um Autor?'),
        queryset=Autor.objects.all(),
        required=False,
        help_text='Se o usuário que está sendo cadastrado (ou em edição) é um usuário para cadastro de proposições, você pode selecionar para que autor ele registrará proposições.')

    class Meta:
        model = get_user_model()
        fields = [
            get_user_model().USERNAME_FIELD,
            'first_name',
            'last_name',
            'is_active',

            'token',

            'new_password1',
            'new_password2',

            'parlamentar',
            'autor',

            'groups',
            'user_permissions',
        ]

        if get_user_model().USERNAME_FIELD != 'email':
            fields.extend(['email'])

    def __init__(self, *args, **kwargs):

        self.user_session = kwargs.pop('user_session', None)
        self.granular = kwargs.pop('granular', None)
        self.instance = kwargs.get('instance', None)

        row_pwd = [
            ('username', 4),
            ('email', 6),
            ('is_active', 2),
            ('first_name', 6),
            ('last_name', 6),
            ('new_password1', 3 if self.instance and self.instance.pk else 6),
            ('new_password2', 3 if self.instance and self.instance.pk else 6),
        ]

        if self.instance and self.instance.pk:
            row_pwd += [
                (
                    FieldWithButtons(
                        'token',
                        StrictButton(
                            'Renovar',
                            id="renovar-token",
                            css_class="btn-outline-primary"),
                        css_class='' if self.instance and self.instance.pk else 'd-none'),
                    6
                )
            ]

        row_pwd += [

            ('parlamentar', 6),
            ('autor', 6),
            ('groups', 12),

        ] + ([('user_permissions', 12)] if not self.granular is None else [])

        row_pwd = to_row(row_pwd)

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(row_pwd)
        super(UserAdminForm, self).__init__(*args, **kwargs)

        self.fields['groups'].widget = forms.CheckboxSelectMultiple()

        self.fields['parlamentar'].choices = [('', '---------')] + [
            (p.id, p) for p in parlamentares_ativos(timezone.now())
        ]

        if not self.instance.pk:
            self.fields['groups'].choices = [
                (g.id, g) for g in Group.objects.exclude(
                    name__in=['Autor', 'Votante']
                ).order_by('name')
            ]

        else:
            operadorautor = self.instance.operadorautor_set.first()
            votante = self.instance.votante_set.first()
            self.fields['token'].initial = self.instance.auth_token.key
            self.fields['autor'].initial = operadorautor.autor if operadorautor else None
            self.fields['parlamentar'].initial = votante.parlamentar if votante else None

            self.fields['groups'].choices = [
                (g.id, g) for g in self.instance.groups.exclude(
                    name__in=['Autor', 'Votante']
                ).order_by('name')
            ] + [
                (g.id, g) for g in Group.objects.exclude(
                    user=self.instance).exclude(
                        name__in=['Autor', 'Votante']
                ).order_by('name')
            ]

            self.fields[
                'user_permissions'].widget = forms.CheckboxSelectMultiple()

            if not self.granular is None:
                self.fields['user_permissions'].choices = [
                    (p.id, p) for p in self.instance.user_permissions.all(
                    ).order_by('content_type__app_label',
                               'content_type__model',
                               'codename')
                ] + [
                    (p.id, p) for p in Permission.objects.filter(
                        content_type__app_label__in=list(
                            map(lambda x: x.split('.')[-1], settings.SAPL_APPS))
                    ).exclude(
                        user=self.instance
                    ).order_by('content_type__app_label',
                               'content_type__model',
                               'codename')
                ]

    def save(self, commit=True):
        if self.cleaned_data['new_password1']:
            self.instance.set_password(self.cleaned_data['new_password1'])
        permissions = None
        votante = None
        operadorautor = None
        if self.instance.id:
            inst_old = get_user_model().objects.get(pk=self.instance.pk)
            if self.granular is None:
                permissions = list(inst_old.user_permissions.all())

            votante = inst_old.votante_set.first()
            operadorautor = inst_old.operadorautor_set.first()

        inst = super().save(commit)

        if permissions:
            inst.user_permissions.add(*permissions)

        g_autor = Group.objects.get(name=SAPL_GROUP_AUTOR)
        g_votante = Group.objects.get(name=SAPL_GROUP_VOTANTE)

        if not self.cleaned_data['autor']:
            inst.groups.remove(g_autor)
            if operadorautor:
                operadorautor.delete()
        else:
            inst.groups.add(g_autor)
            if operadorautor:
                if operadorautor.autor != self.cleaned_data['autor']:
                    operadorautor.autor = self.cleaned_data['autor']
                    operadorautor.save()
            else:
                operadorautor = OperadorAutor()
                operadorautor.user = inst
                operadorautor.autor = self.cleaned_data['autor']
                operadorautor.save()

        if not self.cleaned_data['parlamentar']:
            inst.groups.remove(g_votante)
            if votante:
                votante.delete()
        else:
            inst.groups.add(g_votante)
            if votante:
                if votante.parlamentar != self.cleaned_data['parlamentar']:
                    votante.parlamentar = self.cleaned_data['parlamentar']
                    votante.save()
            else:
                votante = Votante()
                votante.user = inst
                votante.parlamentar = self.cleaned_data['parlamentar']
                votante.save()

        return inst

    def clean(self):
        data = super().clean()

        if self.errors:
            return data

        new_password1 = data.get('new_password1', '')
        new_password2 = data.get('new_password2', '')

        if new_password1 != new_password2:
            raise forms.ValidationError(
                _("As senhas informadas são diferentes"),
            )
        else:
            if new_password1 and new_password2:
                password_validation.validate_password(
                    new_password2, self.instance)

        parlamentar = data.get('parlamentar', None)
        if parlamentar and parlamentar.votante_set.exists() and \
                parlamentar.votante_set.first().user != self.instance:
            raise forms.ValidationError(
                mark_safe(
                    'O Parlamentar <strong>{}</strong> '
                    'já está associado a outro usuário: <strong>{}</strong>.<br>'
                    'Para realizar nova associação, você precisa '
                    'primeiro cancelar esta já existente.'.format(
                        parlamentar,
                        parlamentar.votante_set.first().user
                    ))
            )

        autor = data.get('autor', None)
        if parlamentar and autor:
            if autor.autor_related != parlamentar:
                raise forms.ValidationError(
                    'Um usuário não deve ser Votante de um parlamentar, e operador de um Autor que possui um parlamentar diferente, ou mesmo outro tipo de Autor.'
                )

        """
        
        if 'email' in data and data['email']:
            duplicidade = get_user_model().objects.filter(email=data['email'])
            if self.instance.id:
                duplicidade = duplicidade.exclude(id=self.instance.id)

            if duplicidade.exists():
                raise forms.ValidationError(
                    "Email já cadastrado para: {}".format(
                        ', '.join(map(lambda x: str(x), duplicidade.all())),
                    )
                )"""

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
            self.logger.warning(
                'O número da SessaoLegislativa ({}) é menor ou igual '
                'que o de Sessões Legislativas passadas ({})'.format(
                    numero, ult)
            )
            raise ValidationError('O número da Sessão Legislativa não pode ser menor ou igual '
                                  'que o de Sessões Legislativas passadas')

        if data_inicio < data_inicio_leg or \
                data_inicio > data_fim_leg:
            self.logger.warning(
                'A data de início ({}) da SessaoLegislativa está compreendida '
                'fora da data início ({}) e fim ({}) da Legislatura '
                'selecionada'.format(
                    data_inicio, data_inicio_leg, data_fim_leg)
            )
            raise ValidationError('A data de início da Sessão Legislativa deve estar compreendida '
                                  'entre a data início e fim da Legislatura selecionada')

        if data_fim > data_fim_leg or \
                data_fim < data_inicio_leg:
            self.logger.warning(
                'A data de fim ({}) da SessaoLegislativa está compreendida '
                'fora da data início ({}) e fim ({}) da Legislatura '
                'selecionada.'.format(data_fim, data_inicio_leg, data_fim_leg)
            )
            raise ValidationError('A data de fim da Sessão Legislativa deve estar compreendida '
                                  'entre a data início e fim da Legislatura selecionada')

        if data_inicio > data_fim:
            self.logger.warning(
                'Data início ({}) superior à data fim ({}).'.format(
                    data_inicio, data_fim)
            )
            raise ValidationError(
                'Data início não pode ser superior à data fim')

        if data_fim.year > data_inicio.year + 1:
            raise ValidationError(
                'A Sessão Legislativa só pode ter, no máximo, dois anos de período.')

        data_inicio_intervalo = cleaned_data['data_inicio_intervalo']
        data_fim_intervalo = cleaned_data['data_fim_intervalo']

        if data_inicio_intervalo and data_fim_intervalo and \
                data_inicio_intervalo > data_fim_intervalo:
            self.logger.warning(
                'Data início de intervalo ({}) superior à '
                'data fim de intervalo ({}).'.format(
                    data_inicio_intervalo, data_fim_intervalo)
            )
            raise ValidationError('Data início de intervalo não pode ser '
                                  'superior à data fim de intervalo')

        if data_inicio_intervalo:
            if data_inicio_intervalo < data_inicio or \
                    data_inicio_intervalo < data_inicio_leg or \
                    data_inicio_intervalo > data_fim or \
                    data_inicio_intervalo > data_fim_leg:
                self.logger.warning(
                    'A data de início do intervalo ({}) não está compreendida entre '
                    'as datas de início ({}) e fim ({}) tanto da Legislatura quanto da '
                    'própria Sessão Legislativa ({} e {}).'.format(
                        data_inicio_intervalo, data_inicio_leg, data_fim_leg, data_inicio, data_fim
                    )
                )
                raise ValidationError('A data de início do intervalo deve estar compreendida entre '
                                      'as datas de início e fim tanto da Legislatura quanto da '
                                      'própria Sessão Legislativa')
        if data_fim_intervalo:
            if data_fim_intervalo > data_fim or \
                    data_fim_intervalo > data_fim_leg or \
                    data_fim_intervalo < data_inicio or \
                    data_fim_intervalo < data_inicio_leg:
                self.logger.warning(
                    'A data de fim do intervalo ({}) não está compreendida entre '
                    'as datas de início ({}) e fim ({}) tanto da Legislatura quanto da '
                    'própria Sessão Legislativa ({} e {}).'.format(
                        data_fim_intervalo, data_inicio_leg, data_fim_leg, data_inicio, data_fim
                    )
                )
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

    q = forms.CharField(
        max_length=120, required=False,
        label='Pesquise o nome do Autor com o '
        'tipo Selecionado e marque o escolhido.')

    autor_related = ChoiceWithoutValidationField(label='',
                                                 required=False,
                                                 widget=forms.RadioSelect())

    operadores = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label=_('Usuários do SAPL ligados ao autor acima selecionado'),
        required=False,
        help_text=_(
            'Para ser listado aqui, o usuário não pode estar em nenhum outro autor e deve estar marcado como ativo.')
    )

    class Meta:
        model = Autor
        fields = ['tipo',
                  'nome',
                  'cargo',
                  'autor_related',
                  'q',
                  'operadores'
                  ]

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
        operadores_select = to_row(
            [
                ('operadores', 12)
            ]
        )

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(autor_select, *operadores_select)

        super(AutorForm, self).__init__(*args, **kwargs)

        self.fields['operadores'].choices = [
            (
                u.id,
                u.username,
                u
            )
            for u in get_user_model().objects.filter(
                operadorautor_set__autor=self.instance
            ).order_by('-is_active',
                       get_user_model().USERNAME_FIELD
                       ) if self.instance.id
        ] + [
            (
                u.id,
                u.username,
                u
            )
            for u in get_user_model().objects.filter(
                operadorautor_set__isnull=True,
                is_active=True
            ).order_by('-is_active',
                       get_user_model().USERNAME_FIELD
                       )
        ]

        if self.instance.pk:
            if self.instance.autor_related:
                self.fields['autor_related'].choices = [
                    (self.instance.autor_related.pk,
                     self.instance.autor_related)]

                self.fields['q'].initial = ''

            self.fields['autor_related'].initial = self.instance.autor_related

    def valida_igualdade(self, texto1, texto2, msg):
        if texto1 != texto2:
            self.logger.warning(
                'Textos diferentes. ("{}" e "{}")'.format(texto1, texto2)
            )
            raise ValidationError(msg)
        return True

    def clean(self):
        super(AutorForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cd = self.cleaned_data

        qs_autor = Autor.objects.all()

        if self.instance.pk:
            qs_autor = qs_autor.exclude(pk=self.instance.pk)

        if 'tipo' not in cd or not cd['tipo']:
            self.logger.warning('Tipo do Autor não selecionado.')
            raise ValidationError(
                _('O Tipo do Autor deve ser selecionado.'))

        tipo = cd['tipo']
        if not tipo.content_type:
            if 'nome' not in cd or not cd['nome']:
                self.logger.warning('Nome do Autor não informado.')
                raise ValidationError(
                    _('O Nome do Autor deve ser informado.'))
            elif qs_autor.filter(nome=cd['nome']).exists():
                raise ValidationError("Autor '%s' já existente!" % cd['nome'])
        else:
            if 'autor_related' not in cd or not cd['autor_related']:
                self.logger.warning(
                    'Registro de %s não escolhido para ser '
                    'vinculado ao cadastro de Autor' % tipo.descricao
                )
                raise ValidationError(
                    _('Um registro de %s deve ser escolhido para ser '
                      'vinculado ao cadastro de Autor') % tipo.descricao)

            if not tipo.content_type.model_class().objects.filter(
                    pk=cd['autor_related']).exists():
                self.logger.warning(
                    'O Registro definido (%s-%s) não está na base '
                    'de %s.' % (cd['autor_related'], cd['q'], tipo.descricao)
                )
                raise ValidationError(
                    _('O Registro definido (%s-%s) não está na base de %s.'
                      ) % (cd['autor_related'], cd['q'], tipo.descricao))

            qs_autor_selected = qs_autor.filter(
                object_id=cd['autor_related'],
                content_type_id=cd['tipo'].content_type_id)
            if qs_autor_selected.exists():
                autor = qs_autor_selected.first()
                self.logger.warning(
                    'Já existe um autor Cadastrado para '
                    '%s' % autor.autor_related
                )
                raise ValidationError(
                    _('Já existe um autor Cadastrado para %s'
                      ) % autor.autor_related)

        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        autor = self.instance

        if not autor.tipo.content_type:
            autor.content_type = None
            autor.object_id = None
            autor.autor_related = None
        else:
            autor.autor_related = autor.tipo.content_type.model_class(
            ).objects.get(pk=self.cleaned_data['autor_related'])
            autor.nome = str(autor.autor_related)

        autor = super(AutorForm, self).save(commit)

        return autor


class AutorFilterSet(django_filters.FilterSet):
    nome = django_filters.CharFilter(
        label=_('Nome do Autor'), lookup_expr='icontains')

    class Meta:
        model = Autor
        fields = ['nome']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row0 = to_row([('nome', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Autor'),
                     row0,
                     form_actions(label='Pesquisar')))


class OperadorAutorForm(ModelForm):

    class Meta:
        model = OperadorAutor
        fields = ['user', ]

    def __init__(self, *args, **kwargs):

        row = to_row([('user', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Operador'), row))

        super(OperadorAutorForm, self).__init__(*args, **kwargs)

        self.fields['user'].choices = [
            (
                u.id,
                '{} - {} - {}'.format(
                    u.get_full_name(),
                    getattr(u, u.USERNAME_FIELD),
                    u.email
                )
            )
            for u in get_user_model().objects.all().order_by(
                get_user_model().USERNAME_FIELD
            )
        ]
        self.fields['user'].widget = forms.RadioSelect()


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

        buttons = FormActions(
            *[
                HTML('''
                                                   <div class="form-check">
                                                       <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                       <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                   </div>
                                               ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa'),
                     row0, row1,
                     buttons)
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

        self.filters['data_inicio'].label = 'Período de Abertura (Inicial - Final)'
        self.form.fields['data_inicio'].required = False

        row1 = to_row([('data_inicio', 12)])

        buttons = FormActions(
            *[
                HTML('''
                        <div class="form-check">
                            <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                            <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                        </div>
                    ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Atas das Sessões Plenárias'),
                     row1, buttons, )
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
    
    tipo = django_filters.ChoiceFilter(required=False,
                                      label='Tipo Norma',
                                      choices=choice_tipos_normas,
                                      initial=0)

    class Meta:
        model = NormaJuridica
        fields = ['ano']

    def __init__(self, *args, **kwargs):
        super(RelatorioNormasMesFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['ano'].label = 'Ano'
        self.form.fields['ano'].required = True

        row1 = to_row([('ano', 6), ('tipo', 6)])

        buttons = FormActions(
            *[
                HTML('''
                                            <div class="form-check">
                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                            </div>
                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Normas por mês do ano.'),
                     row1, buttons, )
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

        buttons = FormActions(
            *[
                HTML('''
                                                    <div class="form-check">
                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                    </div>
                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.helper = SaplFormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Fieldset(_('Normas por acessos nos meses do ano.'),
                     row1, buttons)
        )

    def clean(self):
        super(EstatisticasAcessoNormasForm, self).clean()

        return self.cleaned_data


class RelatorioNormasVigenciaFilterSet(django_filters.FilterSet):

    ano = django_filters.ChoiceFilter(required=True,
                                      label='Ano da Norma',
                                      choices=choice_anos_com_normas,
                                      initial=ultimo_ano_com_norma)

    tipo = django_filters.ChoiceFilter(required=False,
                                      label='Tipo Norma',
                                      choices=choice_tipos_normas,
                                      initial=0)

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

        row1 = to_row([('ano', 6), ('tipo', 6)])
        row2 = to_row([('vigencia', 12)])

        buttons = FormActions(
            *[
                HTML('''
                                                    <div class="form-check">
                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                    </div>
                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Normas por vigência.'),
                     row1, row2,
                     buttons, )
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
        super().__init__(*args, **kwargs)

        self.form.fields['exibir_ordem_dia'] = forms.BooleanField(
            required=False, label='Exibir presença das Ordens do Dia')
        self.form.initial['exibir_ordem_dia'] = True

        self.form.fields['exibir_somente_titular'] = forms.BooleanField(
            required=False, label='Exibir somente parlamentares titulares')
        self.form.initial['exibir_somente_titular'] = False

        self.form.fields['exibir_somente_ativo'] = forms.BooleanField(
            required=False, label='Exibir somente parlamentares ativos')
        self.form.initial['exibir_somente_ativo'] = False

        self.form.fields['legislatura'].required = True

        self.filters['data_inicio'].label = 'Período (Inicial - Final)'

        tipo_sessao_ordinaria = self.filters['tipo'].queryset.filter(
            nome='Ordinária')
        if tipo_sessao_ordinaria:
            self.form.initial['tipo'] = tipo_sessao_ordinaria.first()

        row1 = to_row([('legislatura', 4),
                       ('sessao_legislativa', 4),
                       ('tipo', 4)])
        row2 = to_row([('exibir_ordem_dia', 12),
                       ('exibir_somente_titular', 12),
                       ('exibir_somente_ativo', 12)])
        row3 = to_row([('data_inicio', 12)])

        buttons = FormActions(
            *[
                HTML('''
                        <div class="form-check">
                            <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                            <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                        </div>
                    ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Presença dos parlamentares nas sessões plenárias'),
                     row1, row2, row3, buttons, )
        )

    @property
    def qs(self):
        return qs_override_django_filter(self)


class RelatorioHistoricoTramitacaoFilterSet(django_filters.FilterSet):

    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

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

        row4 = to_row([
            ('autoria__autor', 0),
            (Button('pesquisar',
                    'Pesquisar Autor',
                    css_class='btn btn-primary btn-sm'), 2),
            (Button('limpar',
                    'Limpar Autor',
                    css_class='btn btn-primary btn-sm'), 2)
        ])

        buttons = FormActions(
            *[
                HTML('''
                                            <div class="form-check">
                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                            </div>
                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisar'),
                     row1, row2, row3, row4,
                     HTML(autor_label),
                     HTML(autor_modal),
                     buttons, )
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

        buttons = FormActions(
            *[
                HTML('''
                                                    <div class="form-check">
                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                    </div>
                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Tramitações'),
                     row1, row2, row3,
                     buttons, )
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

        buttons = FormActions(
            *[
                HTML('''
                                                                    <div class="form-check">
                                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                                    </div>
                                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Reunião de Comissão'),
                     row1, row2,
                     buttons, )
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

        buttons = FormActions(
            *[
                HTML('''
                                                    <div class="form-check">
                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                    </div>
                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Audiência Pública'),
                     row1, row2,
                     buttons, )
        )


class RelatorioMateriasTramitacaoFilterSet(django_filters.FilterSet):

    materia__ano = django_filters.ChoiceFilter(required=True,
                                               label='Ano da Matéria',
                                               choices=choice_anos_com_materias)

    tramitacao__unidade_tramitacao_destino = django_filters.ModelChoiceFilter(
        queryset=UnidadeTramitacao.objects.all(),
        label=_('Unidade Atual'))

    tramitacao__status = django_filters.ModelChoiceFilter(
        queryset=StatusTramitacao.objects.all(),
        label=_('Status Atual'))

    materia__autores = django_filters.ModelChoiceFilter(
        label='Autor da Matéria',
        queryset=Autor.objects.all())

    @property
    def qs(self):
        parent = super(RelatorioMateriasTramitacaoFilterSet, self).qs
        return parent.distinct().order_by(
            '-materia__ano', 'materia__tipo', '-materia__numero'
        )

    class Meta:
        model = MateriaEmTramitacao
        fields = ['materia__ano', 'materia__tipo',
                  'tramitacao__unidade_tramitacao_destino',
                  'tramitacao__status', 'materia__autores']

    def __init__(self, *args, **kwargs):
        super(RelatorioMateriasTramitacaoFilterSet, self).__init__(
            *args, **kwargs)

        self.filters['materia__tipo'].label = 'Tipo de Matéria'

        row1 = to_row([('materia__ano', 12)])
        row2 = to_row([('materia__tipo', 12)])
        row3 = to_row([('tramitacao__unidade_tramitacao_destino', 12)])
        row4 = to_row([('tramitacao__status', 12)])
        row5 = to_row([('materia__autores', 12)])

        buttons = FormActions(
            *[
                HTML('''
                            <div class="form-check">
                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                            </div>
                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria em Tramitação'),
                     row1, row2, row3, row4, row5,
                     buttons,)
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

        buttons = FormActions(
            *[
                HTML('''
                                    <div class="form-check">
                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                    </div>
                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria por Ano Autor Tipo'),
                     row1,
                     buttons, )
        )


class RelatorioMateriasPorAutorFilterSet(django_filters.FilterSet):

    autoria__autor = django_filters.CharFilter(widget=forms.HiddenInput())

    @property
    def qs(self):
        parent = super().qs
        return parent.distinct().order_by('-ano', '-numero', 'tipo', 'autoria__autor', '-autoria__primeiro_autor')

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
                     'Limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])

        buttons = FormActions(
            *[
                HTML('''
                                            <div class="form-check">
                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                            </div>
                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria por Autor'),
                     row1, row2,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row3,
                     buttons, )
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
            # O campo fax foi ocultado porque não é utilizado.
            'fax': forms.HiddenInput(),
            # 'fax': forms.TextInput(attrs={'class': 'telefone'}),
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

    google_recaptcha_site_key = forms.CharField(
        label=AppConfig._meta.get_field(
            'google_recaptcha_site_key').verbose_name,
        max_length=256,
        required=False,
        help_text=_(
            'Acesse <a target="_blank" href="https://www.google.com/recaptcha">https://www.google.com/recaptcha</a> '
            'para configurar um Recaptcha para sua casa legislativa. '
            'Com Recaptcha configurado seu sapl disponibilizará '
            'Acompanhamentos de Matérias e Documentos Administrativos '
            'e Recuperação de Senha pela opção "Esqueceu sua Senha" '
            'na tela de login. Esta melhoria na foi necessária com o '
            'intuito de coibir recorrentes ataques ao serviço de email.'),
    )

    google_recaptcha_secret_key = forms.CharField(
        label=AppConfig._meta.get_field(
            'google_recaptcha_secret_key').verbose_name,
        max_length=256,
        required=False)

    class Meta:
        model = AppConfig
        fields = ['documentos_administrativos',
                  'sequencia_numeracao_protocolo',
                  'inicio_numeracao_protocolo',
                  'sequencia_numeracao_proposicao',
                  'esfera_federacao',
                  # 'painel_aberto', # TODO: a ser implementado na versão 3.2
                  'texto_articulado_proposicao',
                  'texto_articulado_materia',
                  'texto_articulado_norma',
                  'proposicao_incorporacao_obrigatoria',
                  'protocolo_manual',
                  'cronometro_discurso',
                  'cronometro_aparte',
                  'cronometro_ordem',
                  'cronometro_consideracoes',
                  'mostrar_brasao_painel',
                  'receber_recibo_proposicao',
                  'assinatura_ata',
                  'estatisticas_acesso_normas',
                  'escolher_numero_materia_proposicao',
                  'tramitacao_materia',
                  'tramitacao_documento',
                  'google_recaptcha_site_key',
                  'google_recaptcha_secret_key',
                  'sapl_as_sapn']

    def __init__(self, *args, **kwargs):
        super(ConfiguracoesAppForm, self).__init__(*args, **kwargs)
        self.fields['cronometro_discurso'].widget.attrs['class'] = 'cronometro'
        self.fields['cronometro_aparte'].widget.attrs['class'] = 'cronometro'
        self.fields['cronometro_ordem'].widget.attrs['class'] = 'cronometro'
        self.fields['cronometro_consideracoes'].widget.attrs['class'] = 'cronometro'

    def clean(self):
        cleaned_data = super().clean()

        if not self.is_valid():
            return cleaned_data

        mostrar_brasao_painel = self.cleaned_data.get(
            'mostrar_brasao_painel', False)
        casa = CasaLegislativa.objects.first()

        if not casa:
            self.logger.warning('Não há casa legislativa relacionada.')
            raise ValidationError("Não há casa legislativa relacionada.")

        if not casa.logotipo and mostrar_brasao_painel:
            self.logger.warning(
                'Não há logitipo configurado para esta '
                'CasaLegislativa ({}).'.format(casa)
            )
            raise ValidationError("Não há logitipo configurado para esta "
                                  "Casa legislativa.")

        return cleaned_data


class RecuperarSenhaForm(GoogleRecapthaMixin, PasswordResetForm):

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):

        kwargs['title_label'] = _('Insira o e-mail cadastrado com a sua conta')
        kwargs['action_label'] = _('Enviar')

        super().__init__(*args, **kwargs)

    def clean(self):

        super(RecuperarSenhaForm, self).clean()

        email_existente = get_user_model().objects.filter(
            email=self.data['email']).exists()

        if not email_existente:
            msg = 'Não existe nenhum usuário cadastrado com este e-mail.'
            self.logger.warning(
                'Não existe nenhum usuário cadastrado com este e-mail ({}).'.format(
                    self.data['email'])
            )
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
            self.logger.warning("'Nova Senha' diferente de 'Confirmar Senha'")
            raise ValidationError(
                "'Nova Senha' diferente de 'Confirmar Senha'")

        # TODO: colocar mais regras como: tamanho mínimo,
        # TODO: caracteres alfanuméricos, maiúsculas (?),
        # TODO: senha atual igual a senha anterior, etc

        if len(new_password1) < 6:
            self.logger.warning(
                'A senha informada não tem o mínimo de 6 caracteres.'
            )
            raise ValidationError(
                "A senha informada deve ter no mínimo 6 caracteres")

        username = data['username']
        old_password = data['old_password']
        user = User.objects.get(username=username)

        if user.is_anonymous:
            self.logger.warning(
                'Não é possível alterar senha de usuário anônimo ({}).'.format(
                    username)
            )
            raise ValidationError(
                "Não é possível alterar senha de usuário anônimo")

        if not user.check_password(old_password):
            self.logger.warning(
                'Senha atual informada não confere '
                'com a senha armazenada.'
            )
            raise ValidationError("Senha atual informada não confere "
                                  "com a senha armazenada")

        if user.check_password(new_password1):
            self.logger.warning(
                'Nova senha igual à senha anterior.'
            )
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
            form_actions(label='Salvar'))

    def clean(self):

        cleaned_data = super(PartidoForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        if cleaned_data['data_criacao'] and cleaned_data['data_extincao']:
            if cleaned_data['data_criacao'] > cleaned_data['data_extincao']:
                raise ValidationError(
                    "Certifique-se de que a data de criação seja anterior à data de extinção.")

        return cleaned_data


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

        buttons = FormActions(
            *[
                HTML('''
                                                            <div class="form-check">
                                                                <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                                <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                            </div>
                                                        ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_(''),
                     row1, row2, row3,
                     buttons, )
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
        buttons = FormActions(
            *[
                HTML('''
                                                                    <div class="form-check">
                                                                        <input name="relatorio" type="checkbox" class="form-check-input" id="relatorio">
                                                                        <label class="form-check-label" for="relatorio">Gerar relatório PDF</label>
                                                                    </div>
                                                                ''')
            ],
            Submit('pesquisar', _('Pesquisar'), css_class='float-right',
                   onclick='return true;'),
            css_class='form-group row justify-content-between',
        )

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


class SaplSearchForm(ModelSearchForm):

    def search(self):
        sqs = super().search()

        return sqs.order_by('-last_update')

    """def get_models(self):
        Return a list of the selected models.
        search_models = []

        if self.is_valid():
            for model in self.cleaned_data['models']:
                search_models.append(haystack_get_model(*model.split('.')))

        return search_models

        return ModelSearchForm.get_models(self)"""
