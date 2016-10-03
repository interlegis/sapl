from sapl.crud.base import CrudAux

from .models import LexmlProvedor, LexmlPublicador

LexmlProvedorCrud = CrudAux.build(LexmlProvedor, 'lexml_provedor')
LexmlPublicadorCrud = CrudAux.build(LexmlPublicador, 'lexml_publicador')
