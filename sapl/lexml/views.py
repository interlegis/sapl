from django.http import HttpResponse
from django.shortcuts import render

from sapl.crud.base import CrudAux, Crud
from sapl.lexml.OAIServer import OAIServerFactory, get_config
from sapl.rules import RP_DETAIL, RP_LIST

from .models import LexmlProvedor, LexmlPublicador

LexmlPublicadorCrud = CrudAux.build(LexmlPublicador, 'lexml_publicador')


class LexmlProvedorCrud(Crud):
    model = LexmlProvedor
    help_topic = 'lexml_provedor'
    public = [RP_LIST, RP_DETAIL]

    class DetailView(Crud.DetailView):
        layout_key = 'LexmlProvedorDetail'


def lexml_request(request):
    request_dict = request.GET.copy()
    if request_dict.get('batch_size'):
        del request_dict['batch_size']

    config = get_config(request.get_raw_uri(), int(request.GET.get('batch_size', '10')))
    oai_server = OAIServerFactory(config)
    r = oai_server.handleRequest(request_dict)
    response = r.decode('UTF-8')
    return HttpResponse(response, content_type='text/xml')


def request_search(request, keyword):
    return render(request, "lexml/resultado-pesquisa.html", {"keyword": keyword})
