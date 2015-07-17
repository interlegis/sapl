from braces.views import FormMessagesMixin
from django.core.urlresolvers import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, DetailView

from sessao.models import SessaoPlenaria
from .forms import SessaoPlenariaForm

class SessaoPlenariaListView(ListView):
    model = SessaoPlenaria


class SessaoPlenariaDetailView(DetailView):
    model = SessaoPlenaria


class SessaoPlenariaCreateView(CreateView):
    model = SessaoPlenaria
    # fields = [f.name for f in SessaoPlenaria._meta.fields]
    form_class = SessaoPlenariaForm
    form_invalid_message = u"Something went wrong, post was not saved"

    success_url = reverse_lazy('sessao_list')


class SessaoPlenariaUpdateView(FormMessagesMixin, UpdateView):
    model = SessaoPlenaria
    fields = [f.name for f in SessaoPlenaria._meta.fields]

    success_url = reverse_lazy('sessao_list')

    form_invalid_message = u"Something went wrong, post was not saved"

    def get_form_valid_message(self):
        return u"{0} updated successfully!".format(self.object)


class SessaoPlenariaDeleteView(DeleteView):
    model = SessaoPlenaria
    success_url = reverse_lazy('sessao_list')
