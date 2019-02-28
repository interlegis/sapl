from django.http import HttpResponse

from sapl.crud.base import CrudAux
from sapl.lexml.OAIServer import OAIServerFactory, get_config

from .models import LexmlProvedor, LexmlPublicador

LexmlProvedorCrud = CrudAux.build(LexmlProvedor, 'lexml_provedor')
LexmlPublicadorCrud = CrudAux.build(LexmlPublicador, 'lexml_publicador')


def lexml_request(request):
    config = get_config(request.get_raw_uri(), int(request.GET.get('batch_size', 10)))
    oai_server = OAIServerFactory(config)
    r = oai_server.handleRequest(request.GET)
    response = r.decode('UTF-8')
    return HttpResponse(response, content_type='text/xml')
