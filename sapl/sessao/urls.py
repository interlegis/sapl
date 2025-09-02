from django.urls import include, path, re_path

from sapl.sessao.views import (AdicionarVariasMateriasExpediente,
                               AdicionarVariasMateriasOrdemDia, BancadaCrud,
                               CargoBancadaCrud, ConsideracoesFinaisView,
                               CorrespondenciaCrud, CorrespondenciaEmLoteView,
                               ExpedienteLeituraView, ExpedienteMateriaCrud,
                               ExpedienteView, JustificativaAusenciaCrud,
                               LeituraEmBlocoExpediente,
                               LeituraEmBlocoOrdemDia, MateriaOrdemDiaCrud,
                               MesaView, OcorrenciaSessaoView, OradorCrud,
                               OradorExpedienteCrud, OradorOrdemDiaCrud,
                               OrdemDiaLeituraView, PainelView,
                               PautaSessaoDetailView, PautaSessaoView,
                               PesquisarPautaSessaoView,
                               PesquisarSessaoPlenariaView,
                               PresencaOrdemDiaView, PresencaView,
                               ResumoAtaView, ResumoOrdenacaoView, ResumoView,
                               RetiradaPautaCrud, SessaoCrud,
                               TipoExpedienteCrud, TipoJustificativaCrud,
                               TipoResultadoVotacaoCrud, TipoRetiradaPautaCrud,
                               TipoSessaoCrud, TransferenciaMateriasExpediente,
                               TransferenciaMateriasOrdemDia, VotacaoEditView,
                               VotacaoEmBlocoExpediente,
                               VotacaoEmBlocoNominalView,
                               VotacaoEmBlocoOrdemDia,
                               VotacaoEmBlocoSimbolicaView,
                               VotacaoExpedienteEditView,
                               VotacaoExpedienteView, VotacaoNominalEditView,
                               VotacaoNominalExpedienteDetailView,
                               VotacaoNominalExpedienteEditView,
                               VotacaoNominalExpedienteView,
                               VotacaoNominalTransparenciaDetailView,
                               VotacaoNominalView,
                               VotacaoSimbolicaTransparenciaDetailView,
                               VotacaoView, abrir_votacao, atualizar_mesa,
                               filtra_materias_copia_sessao_ajax,
                               insere_parlamentar_composicao,
                               mudar_ordem_materia_sessao, recuperar_documento,
                               recuperar_materia, recuperar_nome_tipo_sessao,
                               recuperar_numero_sessao_view,
                               recuperar_tramitacao,
                               remove_parlamentar_composicao,
                               reordena_materias, retirar_leitura,
                               sessao_legislativa_legislatura_ajax,
                               verifica_materia_sessao_plenaria_ajax)

from .apps import AppConfig

app_name = AppConfig.name


urlpatterns = [
    path(
        "sessao/",
        include(
            SessaoCrud.get_urls()
            + OradorCrud.get_urls()
            + OradorExpedienteCrud.get_urls()
            + ExpedienteMateriaCrud.get_urls()
            + JustificativaAusenciaCrud.get_urls()
            + MateriaOrdemDiaCrud.get_urls()
            + OradorOrdemDiaCrud.get_urls()
            + RetiradaPautaCrud.get_urls()
            + CorrespondenciaCrud.get_urls()
        ),
    ),
    re_path(
        r"^sessao/(?P<pk>\d+)/correspondencia-em-lote",
        CorrespondenciaEmLoteView.as_view(),
        name="correspondencia_em_lote",
    ),
    path("sessao/<int:pk>/mesa", MesaView.as_view(), name="mesa"),
    path("sessao/mesa/atualizar-mesa/", atualizar_mesa, name="atualizar_mesa"),
    path(
        "sessao/mesa/insere-parlamentar/composicao/",
        insere_parlamentar_composicao,
        name="insere_parlamentar_composicao",
    ),
    path(
        "sessao/mesa/remove-parlamentar-composicao/",
        remove_parlamentar_composicao,
        name="remove_parlamentar_composicao",
    ),
    re_path(r"^sessao/recuperar-documento/", recuperar_documento),
    re_path(r"^sessao/recuperar-materia/", recuperar_materia),
    re_path(r"^sessao/recuperar-tramitacao/", recuperar_tramitacao),
    re_path(
        r"^sessao/recuperar-numero-sessao/",
        recuperar_numero_sessao_view,
        name="recuperar_numero_sessao_view",
    ),
    re_path(
        r"^sessao/recuperar-nome-tipo-sessao/",
        recuperar_nome_tipo_sessao,
        name="recuperar_nome_tipo_sessao",
    ),
    re_path(
        r"^sessao/sessao-legislativa-legislatura-ajax/",
        sessao_legislativa_legislatura_ajax,
        name="sessao_legislativa_legislatura_ajax_view",
    ),
    re_path(
        r"^sessao/filtra-materias-copia-sessao-ajax/",
        filtra_materias_copia_sessao_ajax,
        name="filtra_materias_copia_sessao_ajax_view",
    ),
    re_path(
        r"^sessao/verifica-materia-sessao-plenaria-ajax/",
        verifica_materia_sessao_plenaria_ajax,
        name="verifica_materia_sessao_plenaria_ajax_view",
    ),
    path(
        "sessao/<int:pk>/<int:spk>/abrir-votacao", abrir_votacao, name="abrir_votacao"
    ),
    re_path(
        r"^sessao/(?P<pk>\d+)/reordena/(?P<tipo>[\w\-]+)/(?P<ordenacao>\d+)/$",
        reordena_materias,
        name="reordena_materias",
    ),
    path("sistema/sessao-plenaria/tipo/", include(TipoSessaoCrud.get_urls())),
    path(
        "sistema/sessao-plenaria/tipo-resultado-votacao/",
        include(TipoResultadoVotacaoCrud.get_urls()),
    ),
    path(
        "sistema/sessao-plenaria/tipo-expediente/",
        include(TipoExpedienteCrud.get_urls()),
    ),
    path(
        "sistema/sessao-plenaria/tipo-justificativa/",
        include(TipoJustificativaCrud.get_urls()),
    ),
    path(
        "sistema/sessao-plenaria/tipo-retirada-pauta/",
        include(TipoRetiradaPautaCrud.get_urls()),
    ),
    path("sistema/bancada/", include(BancadaCrud.get_urls())),
    path("sistema/cargo-bancada/", include(CargoBancadaCrud.get_urls())),
    re_path(
        r"^sistema/resumo-ordenacao/",
        ResumoOrdenacaoView.as_view(),
        name="resumo_ordenacao",
    ),
    re_path(
        r"^sessao/(?P<pk>\d+)/adicionar-varias-materias-expediente/",
        AdicionarVariasMateriasExpediente.as_view(),
        name="adicionar_varias_materias_expediente",
    ),
    re_path(
        r"^sessao/(?P<pk>\d+)/adicionar-varias-materias-ordem-dia/",
        AdicionarVariasMateriasOrdemDia.as_view(),
        name="adicionar_varias_materias_ordem_dia",
    ),
    # PAUTA SESSÃO
    path("sessao/pauta-sessao", PautaSessaoView.as_view(), name="pauta_sessao"),
    path(
        "sessao/pauta-sessao/pesquisar-pauta",
        PesquisarPautaSessaoView.as_view(),
        name="pesquisar_pauta",
    ),
    re_path(
        r"^sessao/pauta-sessao/(?P<pk>\d+)/(?:pdf)?$",
        PautaSessaoDetailView.as_view(),
        name="pauta_sessao_detail",
    ),
    # Subnav sessão
    path("sessao/<int:pk>/expediente", ExpedienteView.as_view(), name="expediente"),
    path(
        "sessao/<int:pk>/ocorrencia_sessao",
        OcorrenciaSessaoView.as_view(),
        name="ocorrencia_sessao",
    ),
    path(
        "sessao/<int:pk>/consideracoes_finais",
        ConsideracoesFinaisView.as_view(),
        name="consideracoes_finais",
    ),
    path("sessao/<int:pk>/presenca", PresencaView.as_view(), name="presenca"),
    path("sessao/<int:pk>/painel", PainelView.as_view(), name="painel"),
    path(
        "sessao/<int:pk>/presencaordemdia",
        PresencaOrdemDiaView.as_view(),
        name="presencaordemdia",
    ),
    path(
        "sessao/<int:pk>/votacao_bloco_ordemdia",
        VotacaoEmBlocoOrdemDia.as_view(),
        name="votacao_bloco_ordemdia",
    ),
    path(
        "sessao/<int:pk>/votacao_bloco/votnom",
        VotacaoEmBlocoNominalView.as_view(),
        name="votacaobloconom",
    ),
    path(
        "sessao/<int:pk>/votacao_bloco/votsimb",
        VotacaoEmBlocoSimbolicaView.as_view(),
        name="votacaoblocosimb",
    ),
    path(
        "sessao/<int:pk>/votacao_bloco_expediente",
        VotacaoEmBlocoExpediente.as_view(),
        name="votacao_bloco_expediente",
    ),
    path(
        "sessao/<int:pk>/leitura_bloco_expediente",
        LeituraEmBlocoExpediente.as_view(),
        name="leitura_bloco_expediente",
    ),
    path(
        "sessao/<int:pk>/leitura_bloco_ordem_dia",
        LeituraEmBlocoOrdemDia.as_view(),
        name="leitura_bloco_ordem_dia",
    ),
    path("sessao/<int:pk>/resumo", ResumoView.as_view(), name="resumo"),
    path("sessao/<int:pk>/resumo_ata", ResumoAtaView.as_view(), name="resumo_ata"),
    path(
        "sessao/pesquisar-sessao",
        PesquisarSessaoPlenariaView.as_view(),
        name="pesquisar_sessao",
    ),
    path(
        "sessao/<int:pk>/matordemdia/votnom/<int:oid>/<int:mid>",
        VotacaoNominalView.as_view(),
        name="votacaonominal",
    ),
    path(
        "sessao/<int:pk>/matordemdia/votnom/edit/<int:oid>/<int:mid>",
        VotacaoNominalEditView.as_view(),
        name="votacaonominaledit",
    ),
    path(
        "sessao/<int:pk>/matordemdia/votsec/<int:oid>/<int:mid>",
        VotacaoView.as_view(),
        name="votacaosecreta",
    ),
    path(
        "sessao/<int:pk>/matordemdia/votsec/view/<int:oid>/<int:mid>",
        VotacaoEditView.as_view(),
        name="votacaosecretaedit",
    ),
    path(
        "sessao/<int:pk>/matordemdia/votsimb/<int:oid>/<int:mid>",
        VotacaoView.as_view(),
        name="votacaosimbolica",
    ),
    path(
        "sessao/<int:pk>/matordemdia/votsimbbloco/",
        VotacaoView.as_view(),
        name="votacaosimbolicabloco",
    ),
    path(
        "sessao/<int:pk>/matordemdia/votsimb/view/<int:oid>/<int:mid>",
        VotacaoEditView.as_view(),
        name="votacaosimbolicaedit",
    ),
    path(
        "sessao/<int:pk>/matexp/votnom/<int:oid>/<int:mid>",
        VotacaoNominalExpedienteView.as_view(),
        name="votacaonominalexp",
    ),
    path(
        "sessao/<int:pk>/matexp/votnom/edit/<int:oid>/<int:mid>",
        VotacaoNominalExpedienteEditView.as_view(),
        name="votacaonominalexpedit",
    ),
    path(
        "sessao/<int:pk>/matexp/votnom/detail/<int:oid>/<int:mid>",
        VotacaoNominalExpedienteDetailView.as_view(),
        name="votacaonominalexpdetail",
    ),
    path(
        "sessao/<int:pk>/matexp/votsimb/<int:oid>/<int:mid>",
        VotacaoExpedienteView.as_view(),
        name="votacaosimbolicaexp",
    ),
    path(
        "sessao/<int:pk>/matexp/votsimb/view/<int:oid>/<int:mid>",
        VotacaoExpedienteEditView.as_view(),
        name="votacaosimbolicaexpedit",
    ),
    path(
        "sessao/<int:pk>/matexp/votsec/<int:oid>/<int:mid>",
        VotacaoExpedienteView.as_view(),
        name="votacaosecretaexp",
    ),
    path(
        "sessao/<int:pk>/matexp/votsec/view/<int:oid>/<int:mid>",
        VotacaoExpedienteEditView.as_view(),
        name="votacaosecretaexpedit",
    ),
    path(
        "sessao/<int:pk>/votacao-nominal-transparencia/<int:oid>/<int:mid>",
        VotacaoNominalTransparenciaDetailView.as_view(),
        name="votacao_nominal_transparencia",
    ),
    path(
        "sessao/<int:pk>/votacao-simbolica-transparencia/<int:oid>/<int:mid>",
        VotacaoSimbolicaTransparenciaDetailView.as_view(),
        name="votacao_simbolica_transparencia",
    ),
    re_path(
        r"^sessao/mudar-ordem-materia-sessao/",
        mudar_ordem_materia_sessao,
        name="mudar_ordem_materia_sessao",
    ),
    path(
        "sessao/<int:pk>/matexp/leitura/<int:oid>/<int:mid>",
        ExpedienteLeituraView.as_view(),
        name="leituraexp",
    ),
    path(
        "sessao/<int:pk>/matordemdia/leitura/<int:oid>/<int:mid>",
        OrdemDiaLeituraView.as_view(),
        name="leituraod",
    ),
    path(
        "sessao/<int:pk>/<int:iso>/<int:oid>/retirar-leitura",
        retirar_leitura,
        name="retirar_leitura",
    ),
    path(
        "sessao/<int:pk>/transf-mat-exp",
        TransferenciaMateriasExpediente.as_view(),
        name="transf_mat_exp",
    ),
    path(
        "sessao/<int:pk>/transf-mat-ordemdia",
        TransferenciaMateriasOrdemDia.as_view(),
        name="transf_mat_ordemdia",
    ),
]
