from django.utils.translation import ugettext_lazy as _

from sapl.crud import build_crud

from .models import (DocumentoAcessorioAdministrativo, DocumentoAdministrativo,
                     Protocolo, StatusTramitacaoAdministrativo,
                     TipoDocumentoAdministrativo, TramitacaoAdministrativo)

tipo_documento_administrativo_crud = build_crud(
    TipoDocumentoAdministrativo, '', [

        [_('Tipo Documento Administrativo'),
         [('sigla', 4), ('sigla', 4), ('descricao', 4)]],
    ])

documento_administrativo_crud = build_crud(
    DocumentoAdministrativo, '', [

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
    ])

documento_acessorio_administrativo_crud = build_crud(
    DocumentoAcessorioAdministrativo, '', [

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
    ])

protocolo_crud = build_crud(
    Protocolo, '', [

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
    ])

status_tramitacao_administrativo_crud = build_crud(
    StatusTramitacaoAdministrativo, '', [

        [_('Status Tramitação Administrativo'),
         [('sigla', 3),
            ('sigla', 3),
            ('ind_tramitacao_FIXME', 3),
            ('descricao', 3)],
            [('sigla', 6), ('ind_tramitacao_FIXME', 6)],
            [('descricao', 12)]],
    ])

tramitacao_administrativo_crud = build_crud(
    TramitacaoAdministrativo, '', [

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
    ])
