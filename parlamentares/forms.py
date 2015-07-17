from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import ugettext as _

from .models import (Legislatura, SessaoLegislativa, Coligacao, Partido,
                     Parlamentar, Dependente, Filiacao, Mandato)
from sapl.layout import SaplFormLayout


class LegislaturaForm(forms.ModelForm):

    class Meta:
        model = Legislatura
        exclude = []

    def __init__(self, *args, **kwargs):
        super(LegislaturaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Legislatura'),
             [('id', 3),
              ('id', 3),
              ('data_inicio', 2),
              ('data_fim', 2),
              ('data_eleicao', 2)],
             [('id', 12)],
             [('data_inicio', 4), ('data_fim', 4), ('data_eleicao', 4)]],
        )


class SessaoLegislativaForm(forms.ModelForm):

    class Meta:
        model = SessaoLegislativa
        exclude = []

    def __init__(self, *args, **kwargs):
        super(SessaoLegislativaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Sessão Legislativa'),
             [('numero', 2),
              ('numero', 2),
              ('tipo', 2),
              ('data_inicio', 2),
              ('data_fim', 2),
              ('data_inicio_intervalo', 1),
              ('data_fim_intervalo', 1)],
             [('numero', 3), ('tipo', 3), ('data_inicio', 3), ('data_fim', 3)],
             [('data_inicio_intervalo', 6), ('data_fim_intervalo', 6)]],
        )


class ColigacaoForm(forms.ModelForm):

    class Meta:
        model = Coligacao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(ColigacaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Coligação'),
             [('nome', 3),
              ('nome', 3),
              ('legislatura', 3),
              ('numero_votos', 3)],
             [('nome', 4), ('legislatura', 4), ('numero_votos', 4)]],
        )


class PartidoForm(forms.ModelForm):

    class Meta:
        model = Partido
        exclude = []

    def __init__(self, *args, **kwargs):
        super(PartidoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Partido Político'),
             [('nome', 3),
              ('nome', 3),
              ('sigla', 2),
              ('data_criacao', 2),
              ('data_extincao', 2)],
             [('nome', 6), ('sigla', 6)],
             [('data_criacao', 6), ('data_extincao', 6)]],
        )


class ParlamentarForm(forms.ModelForm):

    class Meta:
        model = Parlamentar
        exclude = []

    def __init__(self, *args, **kwargs):
        super(ParlamentarForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Cadastro do Parlamentar'),
             [('nome_parlamentar', 4), ('login_FIXME', 4), ('ativo', 4)],
             [('nome_completo', 12)],
             [('nivel_instrucao', 4), ('sexo', 4), ('data_nascimento', 4)],
             [('cpf', 4), ('rg', 4), ('titulo_eleitor', 4)],
             [('situacao_militar', 6), ('profissao', 6)],
             [('endereco_web', 12)],
             [('email', 12)],
             [('numero_gab_parlamentar', 4), ('telefone', 4), ('fax', 4)],
             [('endereco_residencia', 6), ('cep_residencia', 6)],
             [('municipio_residencia', 6), ('uf_FIXME', 6)],
             [('telefone_residencia', 6), ('fax_residencia', 6)],
             [('locais_atuacao', 12)],
             [('file_FIXME', 12)],
             [('biografia', 12)],
             [('observacao_FIXME', 12)],
             [('parlamentar_salvar_FIXME', 12)]],
        )


class DependenteForm(forms.ModelForm):

    class Meta:
        model = Dependente
        exclude = []

    def __init__(self, *args, **kwargs):
        super(DependenteForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Dependentes'),
             [('nome', 12)],
             [('tipo', 4), ('sexo', 4), ('data_nascimento', 4)],
             [('cpf', 4), ('rg', 4), ('titulo_eleitor', 4)]],
        )


class FiliacaoForm(forms.ModelForm):

    class Meta:
        model = Filiacao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(FiliacaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Filiações Partidárias '),
             [('partido', 4), ('data', 4), ('data_desfiliacao', 4)]],
        )


class MandatoForm(forms.ModelForm):

    class Meta:
        model = Mandato
        exclude = []

    def __init__(self, *args, **kwargs):
        super(MandatoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Mandato'),
             [('legislatura', 4), ('coligacao', 4), ('votos_recebidos', 4)],
             [('ind_titular_FIXME', 3),
              ('dat_inicio_mandato_FIXME', 3),
              ('data_fim_mandato', 3),
              ('data_expedicao_diploma', 3)],
             [('observacao', 12)]],
        )
