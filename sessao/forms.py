from django import forms
from django.utils.translation import ugettext_lazy as _


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
