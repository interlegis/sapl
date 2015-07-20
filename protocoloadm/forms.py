from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import ugettext as _

from .models import (TipoDocumentoAdministrativo, DocumentoAdministrativo,
                     DocumentoAcessorioAdministrativo, Protocolo,
                     StatusTramitacaoAdministrativo, TramitacaoAdministrativo)
from sapl.layout import SaplFormLayout


class TipoDocumentoAdministrativoForm(forms.ModelForm):

    class Meta:
        model = TipoDocumentoAdministrativo
        exclude = []

    def __init__(self, *args, **kwargs):
        super(TipoDocumentoAdministrativoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Tipo Documento Administrativo'),
             [('sigla', 4), ('sigla', 4), ('descricao', 4)],
             [('sigla', 6), ('descricao', 6)]],
        )


class DocumentoAdministrativoForm(forms.ModelForm):

    class Meta:
        model = DocumentoAdministrativo
        exclude = []

    def __init__(self, *args, **kwargs):
        super(DocumentoAdministrativoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Formulário de Cadastro'),
             [('tipo', 4), ('numero', 4), ('ano', 4)],
             [('data', 6), ('numero_protocolo', 6)],
             [('assunto', 12)],
             [('interessado', 6), ('tramitacao', 6)],
             [('nom_arquivo_FIXME', 12)],
             [('dias_prazo', 4), ('data_fim_prazo', 4), ('observacao', 4)],
             [('observacao', 12)]],

            [_('Indentificação Básica'),
             [('tipo', 4), ('numero', 4), ('ano', 4)],
             [('data', 6), ('numero_protocolo', 6)],
             [('assunto', 12)],
             [('interessado', 6), ('tramitacao', 6)],
             [('nom_arquivo_FIXME', 12)]],

            [_('Outras Informações'),
             [('dias_prazo', 4), ('data_fim_prazo', 4), ('observacao', 4)],
             [('observacao', 12)]],
        )


class DocumentoAcessorioAdministrativoForm(forms.ModelForm):

    class Meta:
        model = DocumentoAcessorioAdministrativo
        exclude = []

    def __init__(self, *args, **kwargs):
        super(DocumentoAcessorioAdministrativoForm, self).__init__(
            *args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Documento Administrativo'),
             [('tipo', 4), ('nome', 4), ('data', 4)],
             [('autor', 12)],
             [('arquivo', 12)],
             [('assunto', 12)]],

            [_('Documento Acessório'),
             [('tipo', 4), ('nome', 4), ('data', 4)],
             [('autor', 12)],
             [('arquivo', 12)],
             [('assunto', 12)]],
        )


class ProtocoloForm(forms.ModelForm):

    class Meta:
        model = Protocolo
        exclude = []

    def __init__(self, *args, **kwargs):
        super(ProtocoloForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Formulário de Cadastro'),
             [('tipo_documento', 4),
              ('num_documento_FIXME', 4),
              ('ano_documento_FIXME', 4)],
             [('dat_documento_FIXME', 6), ('numero', 6)],
             [('txt_assunto_FIXME', 12)],
             [('interessado', 6), ('ind_tramitacao_FIXME', 6)],
             [('nom_arquivo_FIXME', 12)],
             [('num_dias_prazo_FIXME', 4),
              ('dat_fim_prazo_FIXME', 4),
              ('observacao', 4)],
             [('observacao', 12)]],

            [_('Indentificação Básica'),
             [('tipo_documento', 4),
              ('num_documento_FIXME', 4),
              ('ano_documento_FIXME', 4)],
             [('dat_documento_FIXME', 6), ('numero', 6)],
             [('txt_assunto_FIXME', 12)],
             [('interessado', 6), ('ind_tramitacao_FIXME', 6)],
             [('nom_arquivo_FIXME', 12)]],

            [_('Outras Informações'),
             [('num_dias_prazo_FIXME', 4),
              ('dat_fim_prazo_FIXME', 4),
              ('observacao', 4)],
             [('observacao', 12)]],
        )


class StatusTramitacaoAdministrativoForm(forms.ModelForm):

    class Meta:
        model = StatusTramitacaoAdministrativo
        exclude = []

    def __init__(self, *args, **kwargs):
        super(StatusTramitacaoAdministrativoForm, self).__init__(
            *args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Status Tramitação Administrativo'),
             [('sigla', 3),
              ('sigla', 3),
              ('ind_tramitacao_FIXME', 3),
              ('descricao', 3)],
             [('sigla', 6), ('ind_tramitacao_FIXME', 6)],
             [('descricao', 12)]],
        )


class TramitacaoAdministrativoForm(forms.ModelForm):

    class Meta:
        model = TramitacaoAdministrativo
        exclude = []

    def __init__(self, *args, **kwargs):
        super(TramitacaoAdministrativoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = SaplFormLayout(

            [_('Documento Administrativo'),
             [('cod_ult_tram_dest_FIXME', 6), ('unidade_tramitacao_local', 6)],
             [('status', 6), ('unidade_tramitacao_destino', 6)],
             [('data_encaminhamento', 6), ('data_fim_prazo', 6)],
             [('texto', 12)]],

            [_('Tramitação'),
             [('cod_ult_tram_dest_FIXME', 6), ('unidade_tramitacao_local', 6)],
             [('status', 6), ('unidade_tramitacao_destino', 6)],
             [('data_encaminhamento', 6), ('data_fim_prazo', 6)],
             [('texto', 12)]],
        )
