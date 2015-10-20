from django.conf.urls import include, url

from materia.views import (FormularioCadastroView, FormularioSimplificadoView,
                           autor_crud, materia_legislativa_crud, orgao_crud,
                           origem_crud, regime_tramitacao_crud,
                           status_tramitacao_crud, tipo_autor_crud,
                           tipo_documento_crud, tipo_fim_relatoria_crud,
                           tipo_materia_crud, tipo_proposicao_crud,
                           unidade_tramitacao_crud)

urlpatterns = [
    url(r'^sistema/proposicoes/tipo/', include(tipo_proposicao_crud.urls)),
    url(r'^sistema/proposicoes/autor/', include(autor_crud.urls)),
    url(r'^sistema/materia/tipo/', include(tipo_materia_crud.urls)),
    url(r'^sistema/materia/regime-tramitacao/',
        include(regime_tramitacao_crud.urls)),
    url(r'^sistema/materia/tipo-autor/', include(tipo_autor_crud.urls)),
    url(r'^sistema/materia/tipo-documento/',
        include(tipo_documento_crud.urls)),
    url(r'^sistema/materia/tipo-fim-relatoria/',
        include(tipo_fim_relatoria_crud.urls)),
    url(r'^sistema/materia/unidade-tramitacao/',
        include(unidade_tramitacao_crud.urls)),
    url(r'^sistema/materia/origem/', include(origem_crud.urls)),
    url(r'^sistema/materia/autor/', include(autor_crud.urls)),
    url(r'^sistema/materia/status-tramitacao/',
        include(status_tramitacao_crud.urls)),
    url(r'^sistema/materia/orgao/', include(orgao_crud.urls)),
    url(r'^materia/', include(materia_legislativa_crud.urls)),
    url(r'^materia/formulario-simplificado',
        FormularioSimplificadoView.as_view(),
        name='formulario_simplificado'),
    url(r'^materia/formulario-cadastro',
        FormularioCadastroView.as_view(),
        name='formulario_cadastro')
]
