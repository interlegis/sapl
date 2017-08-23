from datetime import date, timedelta

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from floppyforms.widgets import ClearableFileInput

from sapl.crispy_layout_mixin import form_actions, to_row
from sapl.rules import SAPL_GROUP_VOTANTE

from .models import (ComposicaoColigacao, Filiacao, Frente, Legislatura,
                     Mandato, Parlamentar, Votante)


class ImageThumbnailFileInput(ClearableFileInput):
    template_name = 'floppyforms/image_thumbnail.html'


def validar_datas_legislatura(eleicao, inicio, fim, pk=None):

    # Verifica se data de eleição < inicio < fim
    if inicio >= fim or eleicao >= inicio:
        msg_error = _('A data início deve ser menor que a ' +
                      'data fim, e a data eleição deve ser ' +
                      'menor que a data início')
        return [False, msg_error]

    # Verifica se há alguma data cadastrada no intervalo de tempo desejado
    if Legislatura.objects.filter(
            data_inicio__range=[inicio, fim]).exclude(pk=pk).exists()\
        or Legislatura.objects.filter(
            data_fim__range=[inicio, fim]).exclude(pk=pk).exists():
        msg_error = _('Já existe uma legislatura neste intervalo de datas')
        return [False, msg_error]

    # Verifica se há alguma outra data de eleição cadastrada
    if Legislatura.objects.filter(
            data_eleicao=eleicao).exclude(pk=pk).exists():
        msg_error = _('Esta data de eleição já foi cadastrada')
        return [False, msg_error]

    return [True, '']


class MandatoForm(ModelForm):

    class Meta:
        model = Mandato
        fields = ['legislatura', 'coligacao', 'votos_recebidos',
                  'data_inicio_mandato', 'data_fim_mandato',
                  'data_expedicao_diploma', 'titular',
                  'tipo_afastamento', 'observacao', 'parlamentar']
        widgets = {'parlamentar': forms.HiddenInput()}

    def clean(self):
        super(MandatoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data

        existe_mandato = Mandato.objects.filter(
                            parlamentar=data['parlamentar'],
                            legislatura=data['legislatura']).exists()
        if existe_mandato:
            raise ValidationError(_('Mandato nesta legislatura já existe.'))

        return self.cleaned_data


class LegislaturaForm(ModelForm):

    class Meta:
        model = Legislatura
        exclude = []


class LegislaturaCreateForm(LegislaturaForm):

    def clean(self):
        super(LegislaturaCreateForm, self).clean()

        cleaned_data = self.cleaned_data
        eleicao = cleaned_data['data_eleicao']
        inicio = cleaned_data['data_inicio']
        fim = cleaned_data['data_fim']

        valida_datas = validar_datas_legislatura(eleicao, inicio, fim)
        if not valida_datas[0]:
            raise ValidationError(valida_datas[1])
        return cleaned_data


class LegislaturaUpdateForm(LegislaturaCreateForm):

    def clean(self):
        super(LegislaturaUpdateForm, self).clean()

        cleaned_data = super(LegislaturaCreateForm, self).clean()
        eleicao = cleaned_data['data_eleicao']
        inicio = cleaned_data['data_inicio']
        fim = cleaned_data['data_fim']

        valida_datas = validar_datas_legislatura(
            eleicao, inicio, fim, pk=self.instance.pk)
        if not valida_datas[0]:
            raise ValidationError(valida_datas[1])
        return cleaned_data


class ParlamentarForm(ModelForm):

    class Meta:
        model = Parlamentar
        exclude = []
        widgets = {'fotografia': ImageThumbnailFileInput,
                   'biografia': forms.Textarea(
                       attrs={'id': 'texto-rico'})}


class ParlamentarCreateForm(ParlamentarForm):

    legislatura = forms.ModelChoiceField(
        label=_('Legislatura'),
        required=True,
        queryset=Legislatura.objects.all().order_by('-data_inicio'),
        empty_label='----------',
    )

    data_expedicao_diploma = forms.DateField(
        label=_('Expedição do Diploma'),
        required=True,
    )

    @transaction.atomic
    def save(self, commit=True):
        parlamentar = super(ParlamentarCreateForm, self).save(commit)
        legislatura = self.cleaned_data['legislatura']
        Mandato.objects.create(
            parlamentar=parlamentar,
            legislatura=legislatura,
            data_fim_mandato=legislatura.data_fim,
            data_expedicao_diploma=self.cleaned_data['data_expedicao_diploma'])
        return parlamentar


def validar_datas(data_filiacao, data_desfiliacao, parlamentar, filiacao):
    # Verifica se data de desfiliacao é anterior a data de filiacao
    if data_desfiliacao and data_desfiliacao < data_filiacao:
        error_msg = _("A data de desfiliação não pode anterior \
                       à data de filiação")
        return [False, error_msg]

    filiacoes = parlamentar.filiacao_set.order_by('data')
    if not filiacoes.exists():
        return [True, '']

    # data ficticia de desfiliacao
    df_desfiliacao = data_desfiliacao if data_desfiliacao else date.today()

    # se não puder haver filiação no mesmo dia de desfiliação, basta
    # retirar os timedelta abaixo
    range_livre_exigido = Q(
        data__range=[data_filiacao + timedelta(days=1),
                     df_desfiliacao - timedelta(days=1)]) | Q(
        data_desfiliacao__range=[data_filiacao + timedelta(days=1),
                                 df_desfiliacao - timedelta(days=1)])

    filiacao_em_edicao_id = filiacao.pk
    error_msg = None
    # filiação em edição não é a última e está sem data de desfiliação
    if not data_desfiliacao and filiacao_em_edicao_id and\
            filiacao_em_edicao_id != filiacoes.last().pk:
        error_msg = _("Data de desfiliação do parlamentar não pode ser\
                    ausente, se existirem datas de filiação posteriores.")

    # a filiação que está sendo inclusa não tem data de desfiliação mas
    #  já existe outra sem data de desfiliação
    elif not data_desfiliacao and not filiacao_em_edicao_id and\
            not filiacoes.last().data_desfiliacao:
        error_msg = _("O parlamentar não pode se filiar a novo partido sem\
                        antes se desfiliar do partido anterior.")

    if not error_msg:
        # se a filiação é uma edição, a exclui das possibilidades
        if filiacao_em_edicao_id:
            filiacoes = filiacoes.exclude(pk=filiacao_em_edicao_id)

        # testa a intercessão de intervalo com outra filiação
        if filiacoes.filter(range_livre_exigido).exists():
            error_msg = _("A data de filiação e desfiliação não podem estar\
                            no intervalo de outro período de filiação.")

    if not error_msg:
        # passou pelo teste de intervalo mas a data de filiação é maior que
        # a ultima que está em aberto
        if filiacoes.filter(data_desfiliacao__isnull=True,
                            data__lte=data_filiacao).exists():
            error_msg = _("Não pode haver um registro de filiação com data de \
                    filiação igual ou superior a data de filiação em aberto.")

    if error_msg:
        return [False, error_msg]

    return [True, '']


class FiliacaoForm(ModelForm):

    class Meta:
        model = Filiacao
        fields = ['partido',
                  'data',
                  'data_desfiliacao']

    def clean(self):
        super(FiliacaoForm, self).clean()

        if self.errors:
            return self.errors

        filiacao = super(FiliacaoForm, self).save(commit=False)
        validacao = validar_datas(self.cleaned_data['data'],
                                  self.cleaned_data['data_desfiliacao'],
                                  filiacao.parlamentar,
                                  filiacao)

        if not validacao[0]:
            raise ValidationError(validacao[1])

        return self.cleaned_data


class ComposicaoColigacaoForm(ModelForm):

    class Meta:
        model = ComposicaoColigacao
        fields = ['partido']

    def clean(self):
        super(ComposicaoColigacaoForm, self).clean()

        cleaned_data = self.cleaned_data
        pk = self.initial['coligacao_id']
        if (ComposicaoColigacao.objects.filter(
           coligacao_id=pk,
           partido=cleaned_data.get('partido')).exists()):
            msg = _('Esse partido já foi cadastrado nesta coligação.')
            raise ValidationError(msg)
        else:
            if self.errors:
                return self.errors
            return self.cleaned_data


class FrenteForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(FrenteForm, self).__init__(*args, **kwargs)
        self.fields['parlamentares'].queryset = Parlamentar.objects.filter(
            ativo=True).order_by('nome_completo')
        self.fields['parlamentares'].label = _('Parlamentares \
                (Mantenha CTRL pressionado para selecionar vários)')

    class Meta:
        model = Frente
        fields = '__all__'


class VotanteForm(ModelForm):

    username = forms.CharField(
        label=_('Usuário'),
        required=True,
        max_length=30)

    class Meta:
        model = Votante
        fields = ['username']

    def __init__(self, *args, **kwargs):
        row1 = to_row([('username', 4)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Votante'),
                     row1, form_actions(save_label='Salvar'))
        )
        super(VotanteForm, self).__init__(*args, **kwargs)

    def valida_igualdade(self, texto1, texto2, msg):
        if texto1 != texto2:
            raise ValidationError(msg)
        return True

    def clean(self):
        super(VotanteForm, self).clean()

        cd = self.cleaned_data

        username = cd['username']
        user = get_user_model().objects.filter(username=username)
        if not user.exists():
            raise ValidationError(_(
                "{} [{}] {}".format(
                    'Não foi possível vincular usuário. Usuário',
                    username,
                    'não existe')))
        if Votante.objects.filter(user=user[0].pk).exists():
            raise ValidationError(_(
                "{} [{}] {}".format(
                    'Não foi possível vincular usuário. Usuário',
                    username,
                    'já esta vinculado à outro parlamentar')))

        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=False):
        votante = super(VotanteForm, self).save(commit)

        # Cria user
        u = User.objects.get(username=self.cleaned_data['username'])
        # Adiciona user ao grupo
        g = Group.objects.filter(name=SAPL_GROUP_VOTANTE)[0]
        u.groups.add(g)

        votante.user = u
        votante.save()
        return votante
