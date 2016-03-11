from crud.base import Crud

from .models import LexmlProvedor, LexmlPublicador

LexmlProvedorCrud = Crud.build(LexmlProvedor, 'lexml_provedor')
LexmlPublicadorCrud = Crud.build(LexmlPublicador, 'lexml_publicador')
