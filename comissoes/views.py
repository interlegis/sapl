from braces.views import FormMessagesMixin
from django.conf.urls import url
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView, DetailView)

from .forms import ComissaoForm


class Crud(object):

    def __init__(self, model_form, create_title):

        self.model_form = model_form
        self.create_title = create_title

        self.model = model_form._meta.model

        # urls names
        self.namespace = self.model._meta.model_name

        list_url_name = 'list'
        create_url_name = 'create'
        detail_url_name = 'detail'
        update_url_name = 'update'
        delete_url_name = 'delete'

        def with_namespace(url_name):
            return '%s:%s' % (self.namespace, url_name)

        class BaseMixin(object):

            @property
            def title(self):
                return self.get_object()

            help_url = '/comissoes/ajuda'  # FIXME

        class CrudListView(BaseMixin, ListView):
            model = self.model
            title = model._meta.verbose_name_plural

        class CrudCreateView(BaseMixin, CreateView):
            model = self.model
            form_class = ComissaoForm
            title = self.create_title

            def get_success_url(self):
                return reverse(with_namespace(detail_url_name),
                               args=(self.object.id,))

        class CrudDetailView(BaseMixin, DetailView):
            model = self.model

        class CrudUpdateView(BaseMixin, FormMessagesMixin, UpdateView):
            model = self.model
            form_class = ComissaoForm
            success_url = reverse_lazy('comissao_list')
            form_invalid_message = u"Something went wrong, post was not saved"

            def get_form_valid_message(self):
                return u"{0} updated successfully!".format(self.object)

        class CrudDeleteView(BaseMixin, DeleteView):
            model = self.model
            success_url = reverse_lazy('comissao_list')

        self.CrudListView = CrudListView
        self.CrudCreateView = CrudCreateView
        self.CrudDetailView = CrudDetailView
        self.CrudUpdateView = CrudUpdateView
        self.CrudDeleteView = CrudDeleteView

        self.urls = [
            url(r'^$',
                CrudListView.as_view(), name=list_url_name),
            url(r'^create$',
                CrudCreateView.as_view(), name=create_url_name),
            url(r'^(?P<pk>\d+)$',
                CrudDetailView.as_view(), name=detail_url_name),
            url(r'^(?P<pk>\d+)/edit$',
                CrudUpdateView.as_view(), name=update_url_name),
            url(r'^(?P<pk>\d+)/delete$',
                CrudDeleteView.as_view(), name=delete_url_name),
        ], 'comissao', 'comissao'


comissao_crud = Crud(ComissaoForm, _('Nova Comissão'))
