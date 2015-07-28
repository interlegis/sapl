from django.conf.urls import include, url

from comissoes.models import Comissao
from comissoes.urls import comissoes_urls
from sapl.crud import build_crud

crud = build_crud(
    Comissao, '',

    ['Dados Básicos',
     [('nome', 9), ('sigla', 3)],
     [('tipo', 3)]
     ],

    ['Dados Complementares',
     [('finalidade', 12)]
     ],
)

patterns, namespace, app_name = comissoes_urls

urlpatterns = [
    url(r'^comissoes/', include((
        crud.urlpatterns + patterns[len(crud.urlpatterns):],
        namespace, app_name))),
]
