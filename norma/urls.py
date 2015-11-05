from django.conf.urls import url

from norma.views import NormaIncluirView, norma_temporario_para_compilacao_crud

norma_url_patterns = norma_temporario_para_compilacao_crud.urlpatterns

urlpatterns = [
    # url(r'^norma/', include(norma_url_patterns,
    #                         norma_temporario_para_compilacao_crud.namespace,
    #                         norma_temporario_para_compilacao_crud.namespace)),
    # url(r'^sistema/norma/tipo/', include(tipo_norma_crud.urls)),
    # url(r'^sistema/norma/assunto/', include(assunto_norma_crud.urls)),
    url(r'^norma/incluir', NormaIncluirView.as_view(), name='norma-incluir'),
]
