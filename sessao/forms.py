from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import ugettext as _

from .models import (TipoSessaoPlenaria, SessaoPlenaria, ExpedienteMateria,
                     TipoExpediente, OrdemDia, TipoResultadoVotacao,
                     RegistroVotacao)
from sapl.layout import SaplFormLayout


class TipoSessaoPlenariaForm(forms.ModelForm):

    class Meta:
        model = TipoSessaoPlenaria
        exclude = []

    def __init__(self, *args, **kwargs):
        super(TipoSessaoPlenariaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Tipo de Sessão Plenária'),
             [('nome', 6), ('quorum_minimo', 6)],
             [('tipo_sessao_plenaria_salvar_FIXME', 12)]],
        )


class SessaoPlenariaForm(forms.ModelForm):

    class Meta:
        model = SessaoPlenaria
        exclude = []

    def __init__(self, *args, **kwargs):
        super(SessaoPlenariaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Dados Básicos'),
             [('numero', 3),
              ('tip_sessao_plen_FIXME', 3),
              ('legislatura', 3),
              ('sessao_leg_FIXME', 3)],
             [('data_inicio', 12)],
             [('data_fim', 12)],
             [('file_pauta_FIXME', 3),
              ('file_ata_FIXME', 3),
              ('url_audio', 3),
              ('url_video', 3)],
             [('url_audio', 6), ('url_video', 6)],
             [('url_audio', 6), ('url_video', 6)]],
        )


class ExpedienteMateriaForm(forms.ModelForm):

    class Meta:
        model = ExpedienteMateria
        exclude = []

    def __init__(self, *args, **kwargs):
        super(ExpedienteMateriaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Cadastro de Matérias do Expediente'),
             [('data_ordem', 4), ('tip_sessao_FIXME', 4), ('numero_ordem', 4)],
             [('tip_id_basica_FIXME', 4),
              ('num_ident_basica_FIXME', 4),
              ('ano_ident_basica_FIXME', 4)],
             [('tipo_votacao', 12)],
             [('observacao', 12)]],
        )


class TipoExpedienteForm(forms.ModelForm):

    class Meta:
        model = TipoExpediente
        exclude = []

    def __init__(self, *args, **kwargs):
        super(TipoExpedienteForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Tipo de Expediente'),
             [('nome', 12)],
             [('tipo_expediente_salvar_FIXME', 12)]],
        )


class OrdemDiaForm(forms.ModelForm):

    class Meta:
        model = OrdemDia
        exclude = []

    def __init__(self, *args, **kwargs):
        super(OrdemDiaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Cadastro de Matérias da Ordem do Dia'),
             [('data_ordem', 4), ('tip_sessao_FIXME', 4), ('numero_ordem', 4)],
             [('tip_id_basica_FIXME', 4),
              ('num_ident_basica_FIXME', 4),
              ('ano_ident_basica_FIXME', 4)],
             [('tipo_votacao', 12)],
             [('observacao', 12)]],
        )


class TipoResultadoVotacaoForm(forms.ModelForm):

    class Meta:
        model = TipoResultadoVotacao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(TipoResultadoVotacaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Tipo de Resultado da Votação'),
             [('nome', 12)],
             [('tipo_resultado_votacao_salvar_FIXME', 12)]],
        )


class RegistroVotacaoForm(forms.ModelForm):

    class Meta:
        model = RegistroVotacao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(RegistroVotacaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Votação Simbólica'),
             [('numero_votos_sim', 3),
              ('numero_votos_nao', 3),
              ('numero_abstencoes', 3),
              ('nao_votou_FIXME', 3)],
             [('votacao_branco_FIXME', 6),
              ('ind_votacao_presidente_FIXME', 6)],
             [('tipo_resultado_votacao', 12)],
             [('observacao', 12)]],
        )
