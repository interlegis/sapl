from braces.views import FormMessagesMixin
from django.conf.urls import url
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView, DetailView)


class Crud(object):

    def __init__(self, model_form, create_title):

        self.model_form = model_form
        self.create_title = create_title

        self.model = model_form._meta.model

        # urls names
        self.namespace = self.model._meta.model_name

        def in_namespace(url_name):
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
            form_class = model_form
            title = self.create_title

            def get_success_url(self):
                return reverse(in_namespace('detail'), args=(self.object.id,))

        class CrudDetailView(BaseMixin, DetailView):
            model = self.model

        class CrudUpdateView(BaseMixin, FormMessagesMixin, UpdateView):
            model = self.model
            form_class = model_form
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
            url(r'^$', CrudListView.as_view(), name='list'),
            url(r'^create$', CrudCreateView.as_view(), name='create'),
            url(r'^(?P<pk>\d+)$', CrudDetailView.as_view(), name='detail'),
            url(r'^(?P<pk>\d+)/edit$',
                CrudUpdateView.as_view(), name='update'),
            url(r'^(?P<pk>\d+)/delete$',
                CrudDeleteView.as_view(), name='delete'),
        ], self.namespace, self.namespace
