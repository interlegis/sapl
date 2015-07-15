from django.core.urlresolvers import reverse_lazy
from vanilla import CreateView, ListView

from comissoes.models import Comissao


class ListaComissoes(ListView):
    model = Comissao
    context_object_name = 'comissoes'
    template_name = 'comissoes/lista_comissao.html'


class CriarComissao(CreateView):
    model = Comissao
    success_url = reverse_lazy('ListaComissoes')


class DetalheComissao(ListView):
    model = Comissao
    context_object_name = 'comissoes'
