from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from floppyforms.widgets import ClearableFileInput

import sapl

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


def validate(data, data_desfiliacao, parlamentar, filiacao):
    data_filiacao = data
    data_desfiliacao = data_desfiliacao

    # Dá erro caso a data de desfiliação seja anterior a de filiação
    if data_desfiliacao and data_desfiliacao < data_filiacao:
        error_msg = _("A data de desfiliação não pode anterior \
                      à data de filiação")
        return [False, error_msg]

    # Esse bloco garante que não haverá intersecção entre os
    # períodos de filiação
    id_filiacao_atual = filiacao.pk
    todas_filiacoes = parlamentar.filiacao_set.all()

    for filiacoes in todas_filiacoes:
        if (not filiacoes.data_desfiliacao and
                filiacoes.id != id_filiacao_atual):
            error_msg = _("O parlamentar não pode se filiar a algum partido \
                       sem antes se desfiliar do partido anterior")
            return [False, error_msg]

    error_msg = None
    for filiacoes in todas_filiacoes:
        if filiacoes.id != id_filiacao_atual:

            data_init = filiacoes.data
            data_fim = filiacoes.data_desfiliacao

            if data_init <= data_filiacao < data_fim:

                error_msg = _("A data de filiação e \
                        desfiliação não podem estar no intervalo \
                        de outro período de filiação")
                break

            if (data_desfiliacao and
                    data_init < data_desfiliacao < data_fim):

                error_msg = _("A data de filiação e \
                        desfiliação não podem estar no intervalo \
                        de outro período de filiação")
                break

            if (data_desfiliacao and
                data_filiacao <= data_init and
                    data_desfiliacao >= data_fim):

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
        validacao = validate(self.cleaned_data['data'],
                             self.cleaned_data['data_desfiliacao'],
                             filiacao.parlamentar,
                             filiacao)

        if not validacao[0]:
            raise ValidationError(validacao[1])

        return self.cleaned_data
