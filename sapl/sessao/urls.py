from django.conf.urls import include, url

from sapl.sessao.views import (AdicionarVariasMateriasExpediente,
                               AdicionarVariasMateriasOrdemDia, BancadaCrud,
                               BlocoCrud, CargoBancadaCrud,
                               ExpedienteMateriaCrud, ExpedienteView,
                               JustificativaAusenciaCrud, MateriaOrdemDiaCrud, MesaView, 
                               OradorCrud, OradorExpedienteCrud, PainelView,
                               PautaSessaoDetailView, PautaSessaoView,
                               PesquisarPautaSessaoView,
                               PesquisarSessaoPlenariaView,
                               PresencaOrdemDiaView, PresencaView,
                               ResumoOrdenacaoView, ResumoView, ResumoAtaView, SessaoCrud,
                               TipoJustificativaCrud, TipoExpedienteCrud, TipoResultadoVotacaoCrud,
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
                               recuperar_numero_sessao,
                               remove_parlamentar_composicao,
                               reordernar_materias_expediente,
                               reordernar_materias_ordem,
                               sessao_legislativa_legislatura_ajax)

from .apps import AppConfig

app_name = AppConfig.name


urlpatterns = [
    url(r'^sessao/', include(SessaoCrud.get_urls() + OradorCrud.get_urls() +
                             OradorExpedienteCrud.get_urls() +
                             ExpedienteMateriaCrud.get_urls() +
                             MateriaOrdemDiaCrud.get_urls())),

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
    url(r'^sessao/recuperar-numero-sessao/', recuperar_numero_sessao),
    url(r'^sessao/sessao-legislativa-legislatura-ajax/',
        sessao_legislativa_legislatura_ajax),

    url(r'^sessao/(?P<pk>\d+)/(?P<spk>\d+)/abrir-votacao$',
        abrir_votacao,
        name="abrir_votacao"),
    url(r'^sessao/(?P<pk>\d+)/reordenar-expediente$',
        reordernar_materias_expediente,
        name="reordenar_expediente"),
    url(r'^sessao/(?P<pk>\d+)/reordenar-ordem$', reordernar_materias_ordem,
        name="reordenar_ordem"),
    url(r'^sistema/sessao-plenaria/tipo/',
        include(TipoSessaoCrud.get_urls())),
    url(r'^sistema/sessao-plenaria/tipo-resultado-votacao/',
        include(TipoResultadoVotacaoCrud.get_urls())),
    url(r'^sistema/sessao-plenaria/tipo-expediente/',
        include(TipoExpedienteCrud.get_urls())),
    url(r'^sistema/sessao-plenaria/tipo-justificativa/',
         include(TipoJustificativaCrud.get_urls())),
    url(r'^sistema/bancada/',
        include(BancadaCrud.get_urls())),
    url(r'^sistema/bloco/',
        include(BlocoCrud.get_urls())),
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
    url(r'^sessao/pauta-sessao/(?P<pk>\d+)$',
        PautaSessaoDetailView.as_view(), name='pauta_sessao_detail'),

    # Subnav sessão
    url(r'^sessao/(?P<pk>\d+)/expediente$',
        ExpedienteView.as_view(), name='expediente'),
    url(r'^sessao/(?P<pk>\d+)/presenca$',
        PresencaView.as_view(), name='presenca'),
    url(r'^sessao/(?P<pk>\d+)/painel$',
        PainelView.as_view(), name='painel'),
    url(r'^sessao/(?P<pk>\d+)/presencaordemdia$',
        PresencaOrdemDiaView.as_view(),
        name='presencaordemdia'),
    url(r'^sessao/(?P<pk>\d+)/resumo$',
        ResumoView.as_view(), name='resumo'),
    url(r'^sessao/(?P<pk>\d+)/resumo_ata$',
        ResumoAtaView.as_view(), name='resumo_ata'),                             
    url(r'^sessao/pesquisar-sessao$',
        PesquisarSessaoPlenariaView.as_view(), name='pesquisar_sessao'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votnom/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoNominalView.as_view(), name='votacaonominal'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votnom'
        '/edit/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoNominalEditView.as_view(), name='votacaonominaledit'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votsec/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoView.as_view(), name='votacaosecreta'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votsec'
        '/view/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoEditView.as_view(), name='votacaosecretaedit'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votsimb/(?P<oid>\d+)/(?P<mid>\d+)$',
        VotacaoView.as_view(), name='votacaosimbolica'),
    url(r'^sessao/(?P<pk>\d+)/matordemdia/votsimb'
        '/view/(?P<oid>\d+)/(?P<mid>\d+)$',
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
    url(r'^sessao/(?P<pk>\d+)/matexp/votsec/view/(?P<oid>\d+)/(?P<mid>\d+)$',
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
    # Justificativa Ausencia
    url(r'^sessao/(?P<pk>\d+)/justificativa/',
        include(JustificativaAusenciaCrud.get_urls())),
]
