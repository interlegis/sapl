from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

import crispy_layout_mixin
from crispy_layout_mixin import form_actions

from .models import SessaoPlenaria


class PresencaForm(forms.Form):
    presenca = forms.CharField(required=False, initial=False)
    parlamentar = forms.CharField(required=False, max_length=20)


class VotacaoNominalForm(forms.Form):
    pass


class ListMateriaForm(forms.Form):
    error_message = forms.CharField(required=False, label='votacao_aberta')


class MateriaOrdemDiaForm(forms.Form):
    data_sessao = forms.CharField(required=True, label=_('Data da Sessão'))
    numero_ordem = forms.IntegerField(required=True, label=_('Número Ordem'))
    tipo_votacao = forms.IntegerField(required=True, label=_('Tipo Votação'))
    tipo_sessao = forms.IntegerField(required=True, label=_('Tipo da Sessão'))
    ano_materia = forms.IntegerField(required=True, label=_('Ano Matéria'))
    numero_materia = forms.IntegerField(required=True,
                                        label=_('Número Matéria'))
    tipo_materia = forms.IntegerField(required=True, label=_('Tipo Matéria'))
    observacao = forms.CharField(required=False, label=_('Ementa'))
    error_message = forms.CharField(required=False, label=_('Matéria'))


class OradorForm(forms.Form):
    numero_ordem = forms.IntegerField(
        required=True,
        label=_('Ordem de pronunciamento'))
    parlamentar = forms.CharField(required=False, max_length=20)
    url_discurso = forms.CharField(required=False, max_length=100)


class OradorDeleteForm(forms.Form):
    pass


class MesaForm(forms.Form):
    parlamentar = forms.IntegerField(required=True)
    cargo = forms.IntegerField(required=True)


class ExpedienteForm(forms.Form):
    conteudo = forms.CharField(required=False, widget=forms.Textarea)


class VotacaoForm(forms.Form):
    votos_sim = forms.CharField(required=True, label='Sim')
    votos_nao = forms.CharField(required=True, label='Não')
    abstencoes = forms.CharField(required=True, label='Abstenções')
    total_votos = forms.CharField(required=False, label='total')


class VotacaoEditForm(forms.Form):
    pass


class SessaoForm(ModelForm):

    class Meta:
        model = SessaoPlenaria
        fields = ['numero',
                  'tipo',
                  'legislatura',
                  'sessao_legislativa',
                  'data_inicio',
                  'hora_inicio',
                  'iniciada',
                  'data_fim',
                  'hora_fim',
                  'finalizada',
                  'upload_pauta',
                  'upload_ata',
                  'url_audio',
                  'url_video']

        widgets = {
            'hora_inicio': forms.TextInput(attrs={'class': 'hora'}),
            'hora_fim': forms.TextInput(attrs={'class': 'hora'}),
        }

    # def clean_url_audio(self):
    #     url_audio = self.cleaned_data.get('url_audio', False)
    #     if url_audio:
    #         if url_audio.size > 5*1024*1024:
    #             raise ValidationError("Arquivo muito grande. ( > 5mb )")
    #         return url_audio

    # def clean_url_video(self):
    #     url_video = self.cleaned_data.get('url_video', False)
    #     if url_video:
    #         if url_video.size > 5*1024*1024:
    #             raise ValidationError("Arquivo muito grande. ( > 5mb )")
    #         return url_video

    def __init__(self, *args, **kwargs):

        row1 = crispy_layout_mixin.to_row(
            [('numero', 3),
             ('tipo', 3),
             ('legislatura', 3),
             ('sessao_legislativa', 3)])

        row2 = crispy_layout_mixin.to_row(
            [('data_inicio', 4),
             ('hora_inicio', 4),
             ('iniciada', 4)])

        row3 = crispy_layout_mixin.to_row(
            [('data_fim', 4),
             ('hora_fim', 4),
             ('finalizada', 4)])

        row4 = crispy_layout_mixin.to_row(
            [('upload_pauta', 6),
             ('upload_ata', 6)])

        row5 = crispy_layout_mixin.to_row(
            [('url_audio', 6),
             ('url_video', 6)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Dados Básicos'),
                row1,
                row2,
                row3,
                row4,
                row5,
                form_actions()
            )
        )
        super(SessaoForm, self).__init__(*args, **kwargs)
