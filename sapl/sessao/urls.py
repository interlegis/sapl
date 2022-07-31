from django.conf.urls import include, url

from sapl.sessao.views import (AdicionarVariasMateriasExpediente,
                               AdicionarVariasMateriasOrdemDia, BancadaCrud,
                               CargoBancadaCrud, ExpedienteMateriaCrud,
                               ExpedienteView, JustificativaAusenciaCrud,
                               OcorrenciaSessaoView, ConsideracoesFinaisView, MateriaOrdemDiaCrud, OradorOrdemDiaCrud,
                               MesaView, OradorCrud,
                               OradorExpedienteCrud, PainelView,
                               PautaSessaoDetailView, PautaSessaoView,
                               PesquisarPautaSessaoView,
                               PesquisarSessaoPlenariaView,
                               PresencaOrdemDiaView, PresencaView,
                               ResumoOrdenacaoView, ResumoView, ResumoAtaView, RetiradaPautaCrud, SessaoCrud,
                               TipoJustificativaCrud, TipoExpedienteCrud, TipoResultadoVotacaoCrud,
                               TipoExpedienteCrud, TipoResultadoVotacaoCrud, TipoRetiradaPautaCrud,
                               TipoSessaoCrud, VotacaoEditView,
                               VotacaoExpedienteEditView,
                               VotacaoExpedienteView, VotacaoNominalEditView,
                               VotacaoNominalExpedienteDetailView,
                               VotacaoNominalExpedienteEditView,
                               VotacaoNominalExpedienteView,
                               VotacaoNominalTransparenciaDetailView,
                               VotacaoSimbolicaTransparenciaDetailView,
                               VotacaoNominalView, VotacaoView, abrir_votacao,
                               atualizar_mesa, insere_parlamentar_composicao,
                               mudar_ordem_materia_sessao, recuperar_materia,
                               recuperar_numero_sessao_view,
                               remove_parlamentar_composicao,
                               reordena_materias,
                               sessao_legislativa_legislatura_ajax,
                               VotacaoEmBlocoOrdemDia, VotacaoEmBlocoExpediente,
                               VotacaoEmBlocoSimbolicaView, VotacaoEmBlocoNominalView,
                               recuperar_nome_tipo_sessao,
                               ExpedienteLeituraView,
                               OrdemDiaLeituraView,
                               retirar_leitura,
                               TransferenciaMateriasExpediente, TransferenciaMateriasOrdemDia,
                               filtra_materias_copia_sessao_ajax, verifica_materia_sessao_plenaria_ajax,
                               recuperar_tramitacao)


from .apps import AppConfig

app_name = AppConfig.name


urlpatterns = [
    url(r'^sessao/', include(SessaoCrud.get_urls() + OradorCrud.get_urls() +
                             OradorExpedienteCrud.get_urls() +
                             ExpedienteMateriaCrud.get_urls() +
                             JustificativaAusenciaCrud.get_urls() +
                             MateriaOrdemDiaCrud.get_urls() +
                             OradorOrdemDiaCrud.get_urls() +
                             RetiradaPautaCrud.get_urls())),

    url(r'^sessao/(?P<pk>\d+)/mesa$', MesaView.as_view(), name='mesa'),

    url(r'^sessao/mesa/atualizar-mesa/$',
        atualizar_mesa,
        name='atualizar_mesa'),

    url(r'^sessao/mesa/insere-parlamentar/composicao/$',
        insere_parlamentar_composicao,
        name='insere_parlamentar_composicao'),

    url(r'^sessao/mesa/remove-parlamentar-composicao/$',
        remove_parlamentar_composicao,
        name='remove_parlamentar_composicao'),

    url(r'^sessao/recuperar-materia/', recuperar_materia),
    url(r'^sessao/recuperar-tramitacao/', recuperar_tramitacao),
    url(r'^sessao/recuperar-numero-sessao/',
        recuperar_numero_sessao_view,
        name='recuperar_numero_sessao_view'
        ),
    url(r'^sessao/recuperar-nome-tipo-sessao/',
        recuperar_nome_tipo_sessao,
        name='recuperar_nome_tipo_sessao'),
    url(r'^sessao/sessao-legislativa-legislatura-ajax/',
        sessao_legislativa_legislatura_ajax,
        name='sessao_legislativa_legislatura_ajax_view'),
    url(r'^sessao/filtra-materias-copia-sessao-ajax/',
        filtra_materias_copia_sessao_ajax, 
        name='filtra_materias_copia_sessao_ajax_view'),    
    url(r'^sessao/verifica-materia-sessao-plenaria-ajax/',
        verifica_materia_sessao_plenaria_ajax,
        name='verifica_materia_sessao_plenaria_ajax_view'),

    url(r'^sessao/(?P<pk>\d+)/(?P<spk>\d+)/abrir-votacao$',
        abrir_votacao,
        name="abrir_votacao"),

    url(r'^sessao/(?P<pk>\d+)/reordena/(?P<tipo>[\w\-]+)/(?P<ordenacao>\d+)/$', reordena_materias, name="reordena_materias"),

    url(r'^sistema/sessao-plenaria/tipo/',
        include(TipoSessaoCrud.get_urls())),
    url(r'^sistema/sessao-plenaria/tipo-resultado-votacao/',
        include(TipoResultadoVotacaoCrud.get_urls())),
    url(r'^sistema/sessao-plenaria/tipo-expediente/',
        include(TipoExpedienteCrud.get_urls())),
    url(r'^sistema/sessao-plenaria/tipo-justificativa/',
        include(TipoJustificativaCrud.get_urls())),
    url(r'^sistema/sessao-plenaria/tipo-retirada-pauta/',
        include(TipoRetiradaPautaCrud.get_urls())),
    url(r'^sistema/bancada/',
        include(BancadaCrud.get_urls())),
    url(r'^sistema/cargo-bancada/',
        include(CargoBancadaCrud.get_urls())),
    url(r'^sistema/resumo-ordenacao/',
        ResumoOrdenacaoView.as_view(),
        name='resumo_ordenacao'),
    url(r'^sessao/(?P<pk>\d+)/adicionar-varias-materias-expediente/',
        AdicionarVariasMateriasExpediente.as_view(),
        name='adicionar_varias_materias_expediente'),
    url(r'^sessao/(?P<pk>\d+)/adicionar-varias-materias-ordem-dia/',
        AdicionarVariasMateriasOrdemDia.as_view(),
        name='adicionar_varias_materias_ordem_dia'),

    # PAUTA SESSÃO
    url(r'^sessao/pauta-sessao$',
        PautaSessaoView.as_view(), name='pauta_sessao'),
    url(r'^sessao/pauta-sessao/pesquisar-pauta$',
        PesquisarPautaSessaoView.as_view(), name='pesquisar_pauta'),
    url(r'^sessao/pauta-sessao/(?P<pk>\d+)/(?:pdf)?$',
        PautaSessaoDetailView.as_view(), name='pauta_sessao_detail'),

    # Subnav sessão
    url(r'^sessao/(?P<pk>\d+)/expediente$',
        ExpedienteView.as_view(), name='expediente'),
    url(r'^sessao/(?P<pk>\d+)/ocorrencia_sessao$',
        OcorrenciaSessaoView.as_view(), name='ocorrencia_sessao'),
    url(r'^sessao/(?P<pk>\d+)/consideracoes_finais$',
        ConsideracoesFinaisView.as_view(), name='consideracoes_finais'),
    url(r'^sessao/(?P<pk>\d+)/presenca$',
        PresencaView.as_view(), name='presenca'),
    url(r'^sessao/(?P<pk>\d+)/painel$',
        PainelView.as_view(), name='painel'),
    url(r'^sessao/(?P<pk>\d+)/presencaordemdia$',
        PresencaOrdemDiaView.as_view(),
        name='presencaordemdia'),
    url(r'^sessao/(?P<pk>\d+)/votacao_bloco_ordemdia$',
        VotacaoEmBlocoOrdemDia.as_view(),
        name='votacao_bloco_ordemdia'),
    url(r'^sessao/(?P<pk>\d+)/votacao_bloco/votnom$',
        VotacaoEmBlocoNominalView.as_view(), name='votacaobloconom'),
    url(r'^sessao/(?P<pk>\d+)/votacao_bloco/votsimb$',
        VotacaoEmBlocoSimbolicaView.as_view(), name='votacaoblocosimb'),
    url(r'^sessao/(?P<pk>\d+)/votacao_bloco_expediente$',
        VotacaoEmBlocoExpediente.as_view(),
        name='votacao_bloco_expediente'),
    url(r'^sessao/(?P<pk>\d+)/resumo$',
        ResumoView.as_view(), name='resumo'),
    url(r'^sessao/(?P<pk>\d+)/resumo_ata$',
        ResumoAtaView.as_view(), name='resumo_ata'),
    url(r'^sessao/pesquisar-sessao$',
        PesquisarSessaoPlenariaView.as_view(), name='pesquisar_sessao'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votnom/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoNominalView.as_view(), name='votacaonominal'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votnom/edit/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoNominalEditView.as_view(), name='votacaonominaledit'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votsec/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoView.as_view(), name='votacaosecreta'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votsec/view/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoEditView.as_view(), name='votacaosecretaedit'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votsimb/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoView.as_view(), name='votacaosimbolica'),

    url(r'^sessao/(?P<pk>\d+)/matordemdia/votsimbbloco/$',
        VotacaoView.as_view(), name='votacaosimbolicabloco'),

    url(r'^sessao/(?P<pk>\d+)/matordemdia/votsimb/view/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoEditView.as_view(), name='votacaosimbolicaedit'),
    url(r'^sessao/(?P<pk>\d+)/matexp/votnom/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoNominalExpedienteView.as_view(), name='votacaonominalexp'),
    url(r'^sessao/(?P<pk>\d+)/matexp/votnom/edit/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoNominalExpedienteEditView.as_view(),
        name='votacaonominalexpedit'),
    url(r'^sessao/(?P<pk>\d+)/matexp/votnom/detail/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoNominalExpedienteDetailView.as_view(),
        name='votacaonominalexpdetail'),
    url(r'^sessao/(?P<pk>\d+)/matexp/votsimb/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoExpedienteView.as_view(), name='votacaosimbolicaexp'),
    url(r'^sessao/(?P<pk>\d+)/matexp/votsimb/view/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoExpedienteEditView.as_view(), name='votacaosimbolicaexpedit'),
    url(r'^sessao/(?P<pk>\d+)/matexp/votsec/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoExpedienteView.as_view(), name='votacaosecretaexp'),
    url(r'^sessao/(?P<pk>\d+)/matexp/votsec/view/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoExpedienteEditView.as_view(), name='votacaosecretaexpedit'),
    url(r'^sessao/(?P<pk>\d+)/votacao-nominal-transparencia/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoNominalTransparenciaDetailView.as_view(),
        name='votacao_nominal_transparencia'),
    url(r'^sessao/(?P<pk>\d+)/votacao-simbolica-transparencia/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoSimbolicaTransparenciaDetailView.as_view(),
        name='votacao_simbolica_transparencia'),
    url(r'^sessao/mudar-ordem-materia-sessao/',
        mudar_ordem_materia_sessao,
        name='mudar_ordem_materia_sessao'),

    url(r'^sessao/(?P<pk>\d+)/matexp/leitura/(?P<oid>\d+)/(?P<mid>\d+)$',
        ExpedienteLeituraView.as_view(), name='leituraexp'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/leitura/(?P<oid>\d+)/(?P<mid>\d+)$',
        OrdemDiaLeituraView.as_view(), name='leituraod'),

    url(r'^sessao/(?P<pk>\d+)/(?P<iso>\d+)/(?P<oid>\d+)/retirar-leitura$',
        retirar_leitura, name='retirar_leitura'),

    url(r'^sessao/(?P<pk>\d+)/transf-mat-exp$',
        TransferenciaMateriasExpediente.as_view(),
        name="transf_mat_exp"),
    url(r'^sessao/(?P<pk>\d+)/transf-mat-ordemdia$',
        TransferenciaMateriasOrdemDia.as_view(),
        name="transf_mat_ordemdia"),
]
