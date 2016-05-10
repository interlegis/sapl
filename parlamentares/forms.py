from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from floppyforms.widgets import ClearableFileInput

import sapl
from sapl.utils import intervalos_tem_intersecao

from .models import Filiacao, Legislatura, Mandato, Parlamentar


class ImageThumbnailFileInput(ClearableFileInput):
    template_name = 'floppyforms/image_thumbnail.html'


class ParlamentarForm(ModelForm):

    class Meta:
        model = Parlamentar
        exclude = []
        widgets = {'fotografia': sapl.utils.ImageThumbnailFileInput,
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

    filiacao_atual_id = filiacao.pk
    # recupera filiacoes em ordem crescente de data
    todas_filiacoes = parlamentar.filiacao_set.all().order_by('data')
    filiacoes_id = [parlamentar.pk for parlamentar in todas_filiacoes]

    # Novo registro inserido com filiacoes ja existentes
    if filiacao_atual_id not in filiacoes_id and len(filiacoes_id) > 0:
            ultima_filiacao = todas_filiacoes.last()
            # Se ultima filiacao aberta e insercao posterior a esta filiacao
            if (not ultima_filiacao.data_desfiliacao and
                data_filiacao >= ultima_filiacao.data):
                    error_msg = _("O parlamentar não pode se filiar \
                                   a novo partido sem antes se \
                                   desfiliar do partido anterior")
                    return [False, error_msg]

            primeira_filiacao = todas_filiacoes.first()

            # se novo registro tem data de desfiliacao aberta
            # e eh anterior a primeira data de filiacao já existente.
            if (not data_desfiliacao and
                data_filiacao <= primeira_filiacao.data):
                    error_msg = _("O parlamentar não pode se filiar \
                                   ,sem uma data de desfiliação, \
                                   a algum partido anterior")
                    return [False, error_msg]

    # checa intervalos de interseccao
    error_msg = None
    for filiacoes in todas_filiacoes:
        # nao comparar o registro com ele mesmo
        if filiacoes.id != filiacao_atual_id:

            # Se a atualizacao eh para remover a data de desfiliacao
            if not data_desfiliacao:
                # so permite na ultima data (ou a unica)
                if filiacao_atual_id != filiacoes_id[-1]:
                    error_msg = _("Data de desfiliação do parlamentar não \
                                   pode ser ausente, se existirem datas de \
                                   filiação posteriores")
                    return [False, error_msg]
            else:
                data_inicio = filiacoes.data
                data_fim = filiacoes.data_desfiliacao

                # Se ainda desfiliado, preenche uma desfiliacao ficticia
                # para fins de checagem de interseccao
                if not data_fim:
                    data_fim = date.today()

                # finalmente verifica intersecao
                if intervalos_tem_intersecao(data_inicio, data_fim,
                                             data_filiacao, data_desfiliacao):
                    error_msg = _("A data de filiação e \
                                   desfiliação não podem estar no intervalo \
                                   de outro período de filiação")
                    break
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
