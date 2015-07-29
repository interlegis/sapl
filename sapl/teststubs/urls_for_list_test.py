from django.conf.urls import include, url

from comissoes.models import Comissao
from comissoes.urls import comissao_url_patterns
from sapl.crud import build_crud

crud = build_crud(
    Comissao, '', [

        ['Dados Básicos',
         [('nome', 9), ('sigla', 3)],
            [('tipo', 3)]
         ],

        ['Dados Complementares',
         [('finalidade', 12)]
         ],
    ])

urlpatterns = [
    url(r'^comissoes/', include((
        crud.urlpatterns + comissao_url_patterns[len(crud.urlpatterns):],
        crud.namespace, crud.namespace))),
]
