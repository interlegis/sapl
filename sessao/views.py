from braces.views import FormMessagesMixin
from django.core.urlresolvers import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, DetailView

from sessao.models import SessaoPlenaria


class SessaoListView(ListView):
    model = SessaoPlenaria


class SessaoDetailView(DetailView):
    model = SessaoPlenaria


class SessaoCreateView(CreateView):
    model = SessaoPlenaria
    success_url = reverse_lazy('sessao_list')


class SessaoUpdateView(FormMessagesMixin, UpdateView):
    model = SessaoPlenaria
    fields = [f.name for f in SessaoPlenaria._meta.fields]

    success_url = reverse_lazy('sessao_list')

    form_invalid_message = u"Something went wrong, post was not saved"

    def get_form_valid_message(self):
        return u"{0} updated successfully!".format(self.object)


class SessaoDeleteView(DeleteView):
    model = SessaoPlenaria
    success_url = reverse_lazy('sessao_list')
