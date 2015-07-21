from braces.views import FormMessagesMixin
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView, DetailView)

from .forms import ComissaoForm
from .models import Comissao


class BaseMixin(object):

    @property
    def title(self):
        return self.get_object()

    help_url = '/comissoes/ajuda'


class ComissaoListView(BaseMixin, ListView):
    model = Comissao
    title = Comissao._meta.verbose_name_plural


class ComissaoDetailView(BaseMixin, DetailView):
    model = Comissao


class ComissaoCreateView(BaseMixin, CreateView):
    model = Comissao
    success_url = reverse_lazy('comissao_list')
    title = _('Nova Comissão')


class ComissaoUpdateView(BaseMixin, FormMessagesMixin, UpdateView):
    model = Comissao
    form_class = ComissaoForm
    success_url = reverse_lazy('comissao_list')
    form_invalid_message = u"Something went wrong, post was not saved"

    def get_form_valid_message(self):
        return u"{0} updated successfully!".format(self.object)


class ComissaoDeleteView(BaseMixin, DeleteView):
    model = Comissao
    success_url = reverse_lazy('comissao_list')
