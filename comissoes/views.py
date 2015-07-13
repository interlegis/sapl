from vanilla import CreateView, DeleteView, ListView, UpdateView
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, get_object_or_404

from comissoes.models import Comissao

class ListaComissoes(ListView):
    model = Comissao
    context_object_name = 'comissoes'
    template_name = 'comissoes/lista_comissao.html'

class CriarComissao(CreateView):
    model = Comissao
    success_url = reverse_lazy('ListaComissoes')
    #template_name = 'comissoes/criar_comissao.html'
    #fields = ['']

class DetalheComissao(ListView):
    model = Comissao
    context_object_name = 'comissoes'