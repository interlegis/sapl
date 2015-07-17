from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import ugettext as _

from .models import (Origem, MateriaLegislativa, Anexada, TipoAutor, Autor,
                     Autoria, DocumentoAcessorio, Numeracao, Orgao, Relatoria,
                     TipoProposicao, Proposicao, StatusTramitacao, UnidadeTramitacao, Tramitacao, )
from sapl.layout import SaplFormLayout


class OrigemForm(forms.ModelForm):

    class Meta:
        model = Origem
        exclude = []

    def __init__(self, *args, **kwargs):
        super(OrigemForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Origem'),
             [('nome', 4), ('nome', 4), ('sigla', 4)],
             [('nome', 6), ('sigla', 6)]],
        )


class MateriaLegislativaForm(forms.ModelForm):

    class Meta:
        model = MateriaLegislativa
        exclude = []

    def __init__(self, *args, **kwargs):
        super(MateriaLegislativaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Identificação Básica'),
             [('tipo', 4), ('numero', 4), ('ano', 4)],
             [('data_apresentacao', 4),
              ('num_protocolo_spdo_FIXME', 4),
              ('tipo_apresentacao', 4)],
             [('nom_arquivo_FIXME', 6), ('modelo_FIXME', 6)]],

            [_('Proposição Eletrônica')],

            [_('Outras Informações'),
             [('apelido', 4), ('dias_prazo', 4), ('polemica', 4)],
             [('objeto', 4), ('regime_tramitacao', 4), ('em_tramitacao', 4)],
             [('data_fim_prazo', 3),
              ('data_publicacao', 3),
              ('complementar', 3),
              ('txt_cep_FIXME', 3)]],

            [_('Origem Externa'),
             [('tipo_origem_externa', 4),
              ('numero_origem_externa', 4),
              ('ano_origem_externa', 4)],
             [('local_origem_externa', 6), ('data_origem_externa', 6)]],

            [_('Dados Textuais'),
             [('ementa', 12)],
             [('indexacao', 12)],
             [('observacao', 12)]],
        )


class AnexadaForm(forms.ModelForm):

    class Meta:
        model = Anexada
        exclude = []

    def __init__(self, *args, **kwargs):
        super(AnexadaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Matéria Legislativa'),
             [('tip_id_basica_FIXME', 4),
              ('num_ident_basica_FIXME', 4),
              ('ano_ident_basica_FIXME', 4)],
             [('data_anexacao', 6), ('data_desanexacao', 6)]],

            [_('Matéria Anexada'),
             [('tip_id_basica_FIXME', 4),
              ('num_ident_basica_FIXME', 4),
              ('ano_ident_basica_FIXME', 4)],
             [('data_anexacao', 6), ('data_desanexacao', 6)]],
        )


class TipoAutorForm(forms.ModelForm):

    class Meta:
        model = TipoAutor
        exclude = []

    def __init__(self, *args, **kwargs):
        super(TipoAutorForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Tipo Autor'),
             [('descricao', 4), ('descricao', 4), ('descricao', 4)],
             [('descricao', 6), ('descricao', 6)]],
        )


class AutorForm(forms.ModelForm):

    class Meta:
        model = Autor
        exclude = []

    def __init__(self, *args, **kwargs):
        super(AutorForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Autor'),
             [('tipo', 6), ('nome', 6)],
             [('autor_eh_usuario_FIXME', 12)],
             [('login_FIXME', 12)]],

            [_('Acesso ao SAPL'),
             [('autor_eh_usuario_FIXME', 12)],
             [('login_FIXME', 12)]],
        )


class AutoriaForm(forms.ModelForm):

    class Meta:
        model = Autoria
        exclude = []

    def __init__(self, *args, **kwargs):
        super(AutoriaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Autoria'),
             [('tip_autor_FIXME', 4),
              ('nom_autor_FIXME', 4),
              ('primeiro_autor', 4)]],
        )


class DocumentoAcessorioForm(forms.ModelForm):

    class Meta:
        model = DocumentoAcessorio
        exclude = []

    def __init__(self, *args, **kwargs):
        super(DocumentoAcessorioForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Documento Acessório'),
             [('tipo', 6), ('nome', 6)],
             [('data', 6), ('autor', 6)],
             [('nom_arquivo_FIXME', 12)],
             [('ementa', 12)],
             [('txt_observacao_FIXME', 12)]],
        )


class NumeracaoForm(forms.ModelForm):

    class Meta:
        model = Numeracao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(NumeracaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Numeração'),
             [('tipo_materia', 6), ('numero_materia', 6)],
             [('ano_materia', 6), ('data_materia', 6)]],
        )


class OrgaoForm(forms.ModelForm):

    class Meta:
        model = Orgao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(OrgaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Órgão'),
             [('nome', 2),
              ('nome', 2),
              ('sigla', 2),
              ('ind_unidade_deliberativa_FIXME', 2),
              ('endereco', 2),
              ('telefone', 2)],
             [('nome', 4),
              ('sigla', 4),
              ('ind_unidade_deliberativa_FIXME', 4)],
             [('endereco', 6), ('telefone', 6)]],
        )


class RelatoriaForm(forms.ModelForm):

    class Meta:
        model = Relatoria
        exclude = []

    def __init__(self, *args, **kwargs):
        super(RelatoriaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Relatoria'),
             [('data_designacao_relator', 12)],
             [('dados_FIXME', 12)],
             [('data_destituicao_relator', 6), ('tipo_fim_relatoria', 6)]],
        )


class TipoProposicaoForm(forms.ModelForm):

    class Meta:
        model = TipoProposicao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(TipoProposicaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Tipo Proposição'),
             [('tipo_proposicao_FIXME', 3),
              ('tipo_proposicao_FIXME', 3),
              ('mat_ou_doc_FIXME', 2),
              ('mat_ou_doc_FIXME', 2),
              ('modelo_FIXME', 2)],
             [('tipo_proposicao_FIXME', 12)],
             [('mat_ou_doc_FIXME', 6), ('mat_ou_doc_FIXME', 6)],
             [('modelo_FIXME', 12)]],
        )


class ProposicaoForm(forms.ModelForm):

    class Meta:
        model = Proposicao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(ProposicaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Proposição'),
             [('tipo', 4), ('dat_criacao_FIXME', 4), ('data_recebimento', 4)],
             [('descricao_FIXME', 12)],
             [('tip_id_basica_FIXME', 4),
              ('num_ident_basica_FIXME', 4),
              ('ano_ident_basica_FIXME', 4)],
             [('nom_arquivo_FIXME', 6), ('modelo_FIXME', 6)]],
        )


class StatusTramitacaoForm(forms.ModelForm):

    class Meta:
        model = StatusTramitacao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(StatusTramitacaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Status Tramitação'),
             [('sigla', 3),
              ('sigla', 3),
              ('ind_tramitacao_FIXME', 3),
              ('descricao', 3)],
             [('sigla', 6), ('ind_tramitacao_FIXME', 6)],
             [('descricao', 12)]],
        )


class UnidadeTramitacaoForm(forms.ModelForm):

    class Meta:
        model = UnidadeTramitacao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(UnidadeTramitacaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Unidade Tramitação'),
             [('orgao', 6), ('cod_unid_spdo_FIXME', 6)],
             [('comissao', 12)],
             [('parlamentar', 12)]],
        )


class TramitacaoForm(forms.ModelForm):

    class Meta:
        model = Tramitacao
        exclude = []

    def __init__(self, *args, **kwargs):
        super(TramitacaoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Tramitação'),
             [('cod_ult_tram_dest_FIXME', 6), ('unidade_tramitacao_local', 6)],
             [('status', 4), ('turno', 4), ('urgente', 4)],
             [('unidade_tramitacao_destino', 4),
              ('data_encaminhamento', 4),
              ('data_fim_prazo', 4)],
             [('texto', 12)]],
        )
