from datetime import date, timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from floppyforms.widgets import ClearableFileInput

from .models import (ComposicaoColigacao, Filiacao, Legislatura, Mandato,
                     Parlamentar)


class ImageThumbnailFileInput(ClearableFileInput):
    template_name = 'floppyforms/image_thumbnail.html'


class LegislaturaForm(ModelForm):

    class Meta:
        model = Legislatura
        exclude = []

    def clean(self):
        cleaned_data = self.cleaned_data
        data_inicio = cleaned_data['data_inicio']
        data_fim = cleaned_data['data_fim']
        data_eleicao = cleaned_data['data_eleicao']

        if data_inicio >= data_fim or data_eleicao >= data_inicio:
            raise ValidationError(_('A data início deve ser menor que a ' +
                                    'data fim, e a data eleição deve ser ' +
                                    'menor que a data início'))

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
