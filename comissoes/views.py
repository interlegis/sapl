from braces.views import FormMessagesMixin
from django.core.urlresolvers import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, DetailView

from comissoes.models import Comissao
from .forms import ComissaoForm


class ComissaoListView(ListView):
    model = Comissao


class ComissaoDetailView(DetailView):
    model = Comissao


class ComissaoCreateView(CreateView):
    model = Comissao
    success_url = reverse_lazy('comissao_list')


class ComissaoUpdateView(FormMessagesMixin, UpdateView):
    model = Comissao
    form_class = ComissaoForm
    success_url = reverse_lazy('comissao_list')
    form_invalid_message = u"Something went wrong, post was not saved"

    def get_form_valid_message(self):
        return u"{0} updated successfully!".format(self.object)


class ComissaoDeleteView(DeleteView):
    model = Comissao
    success_url = reverse_lazy('comissao_list')
