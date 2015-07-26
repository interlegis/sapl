from django.conf.urls import include, url
from sapl.crud import build_crud

from comissoes.models import Comissao


crud = build_crud(
    Comissao,

    ['Dados Básicos',
     [('nome', 9), ('sigla', 3)],
     [('tipo', 3)]
     ],

    ['Dados Complementares',
     [('finalidade', 12)]
     ],
)

urlpatterns = [
    url(r'^comissoes/', include(crud.urls)),
]
