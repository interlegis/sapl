from django.conf.urls import include, url
from parlamentares.views import (MesaDiretoraView, ParlamentaresCadastroView,
                                 ParlamentaresDependentesEditView,
                                 ParlamentaresDependentesView,
                                 ParlamentaresEditarView, ParlamentaresView,
                                 cargo_mesa_crud, coligacao_crud,
                                 legislatura_crud, nivel_instrucao_crud,
                                 partido_crud, sessao_legislativa_crud,
                                 tipo_afastamento_crud, tipo_dependente_crud,
                                 tipo_militar_crud)

urlpatterns = [
    url(r'^sistema/parlamentares/legislatura/',
        include(legislatura_crud.urls)),
    url(r'^sistema/parlamentares/tipo-dependente/',
        include(tipo_dependente_crud.urls)),
    url(r'^sistema/parlamentares/nivel-instrucao/',
        include(nivel_instrucao_crud.urls)),
    url(r'^sistema/parlamentares/coligacao/', include(coligacao_crud.urls)),
    url(r'^sistema/parlamentares/tipo-afastamento/',
        include(tipo_afastamento_crud.urls)),
    url(r'^sistema/parlamentares/tipo-militar/',
        include(tipo_militar_crud.urls)),
    url(r'^sistema/parlamentares/partido/', include(partido_crud.urls)),

    url(r'^sistema/mesa-diretora/sessao-legislativa/',
        include(sessao_legislativa_crud.urls)),
    url(r'^sistema/mesa-diretora/cargo-mesa/',
        include(cargo_mesa_crud.urls)),

    url(r'^parlamentares/$',
        ParlamentaresView.as_view(), name='parlamentares'),
    url(r'^parlamentares/(?P<pk>\d+)/cadastro$',
        ParlamentaresCadastroView.as_view(), name='parlamentares_cadastro'),
    url(r'^parlamentares/(?P<pk>\d+)/dependentes$',
        ParlamentaresDependentesView.as_view(), name='parlamentares_dependentes'),
    url(r'^parlamentares/(?P<pk>\d+)/dependentes/(?P<dk>\d+)$',
        ParlamentaresDependentesEditView.as_view(), name='parlamentares_dependentes_edit'),


    url(r'^parlamentares/(?P<pk>\d+)/(?P<pid>\d+)/editar$',
        ParlamentaresEditarView.as_view(), name='parlamentares_editar'),

    url(r'^mesa-diretora/$',
        MesaDiretoraView.as_view(), name='mesa_diretora'),
]
