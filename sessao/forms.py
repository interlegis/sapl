from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Fieldset, Layout
from django import forms
from django.forms import ModelForm

import sapl
from sapl.layout import form_actions

from .models import AcompanharMateria, SessaoPlenaria


class PresencaForm(forms.Form):
    presenca = forms.CharField(required=False, initial=False)
    parlamentar = forms.CharField(required=False, max_length=20)


class VotacaoNominalForm(forms.Form):
    pass


class ListMateriaForm(forms.Form):
    error_message = forms.CharField(required=False, label='votacao_aberta')


class MateriaOrdemDiaForm(forms.Form):
    data_sessao = forms.CharField(required=True, label='Data da Sessão')
    numero_ordem = forms.IntegerField(required=True, label='Número Ordem')
    tipo_votacao = forms.IntegerField(required=True, label='Tipo Votação')
    tipo_sessao = forms.IntegerField(required=True, label='Tipo da Sessão')
    ano_materia = forms.IntegerField(required=True, label='Ano Matéria')
    numero_materia = forms.IntegerField(required=True, label='Número Matéria')
    tipo_materia = forms.IntegerField(required=True, label='Tipo Matéria')
    observacao = forms.CharField(required=False, label='Ementa')
    error_message = forms.CharField(required=False, label='Matéria')


class OradorForm(forms.Form):
    numero_ordem = forms.IntegerField(
        required=True,
        label='Ordem de pronunciamento')
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


class AcompanharMateriaForm(ModelForm):

    class Meta:
        model = AcompanharMateria
        fields = ['email']

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row([('email', 10)])

        row1.append(
            Column(form_actions(save_label='Cadastrar'), css_class='col-md-2')
            )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Acompanhamento de Matéria por e-mail', row1
            )
        )
        super(AcompanharMateriaForm, self).__init__(*args, **kwargs)


class SessaoForm(ModelForm):

    hora_inicio = forms.CharField(label='Horário Inicio',
                                  required=True,
                                  widget=forms.TextInput(
                                   attrs={'class': 'hora'}))

    hora_fim = forms.CharField(label='Horário Fim',
                               required=True,
                               widget=forms.TextInput(
                                attrs={'class': 'hora'}))

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

    def __init__(self, *args, **kwargs):

        row1 = sapl.layout.to_row(
            [('numero', 3),
             ('tipo', 3),
             ('legislatura', 3),
             ('sessao_legislativa', 3)])

        row2 = sapl.layout.to_row(
            [('data_inicio', 4),
             ('hora_inicio', 4),
             ('iniciada', 4)])

        row3 = sapl.layout.to_row(
            [('data_fim', 4),
             ('hora_fim', 4),
             ('finalizada', 4)])

        row4 = sapl.layout.to_row(
            [('upload_pauta', 6),
             ('upload_ata', 6)])

        row5 = sapl.layout.to_row(
            [('url_audio', 6),
             ('url_video', 6)])

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Dados Básicos',
                row1,
                row2,
                row3,
                row4,
                row5,
                form_actions()
            )
        )
        super(SessaoForm, self).__init__(*args, **kwargs)
