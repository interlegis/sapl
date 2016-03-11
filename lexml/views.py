from crud.base import Crud

from .models import LexmlProvedor, LexmlPublicador

lexml_provedor_crud = Crud.build(LexmlProvedor, 'lexml_provedor')
lexml_publicador_crud = Crud.build(LexmlPublicador, 'lexml_publicador')
