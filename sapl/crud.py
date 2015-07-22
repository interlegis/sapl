from braces.views import FormMessagesMixin
from django.conf.urls import url
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView, DetailView)


class Crud(object):

    def __init__(self, model_form):

        self.model_form = model_form

        self.model = model_form._meta.model

        # urls names
        self.namespace = self.model._meta.model_name

        def in_namespace(url_name):
            return '%s:%s' % (self.namespace, url_name)

        def make_form_invalid_message(msg):
            return '%s %s' % (_('Formulário inválido.'), msg)

        class BaseMixin(object):

            @property
            def title(self):
                return self.get_object()

            list_url = reverse_lazy(in_namespace('list'))
            create_url = reverse_lazy(in_namespace('create'))
            help_url = '/comissoes/ajuda'  # FIXME

            def get_url_for_this_object(self, url_name):
                return reverse(in_namespace(url_name), args=(self.object.id,))

            @property
            def detail_url(self):
                return self.get_url_for_this_object('detail')

            @property
            def update_url(self):
                return self.get_url_for_this_object('detail')

            @property
            def delete_url(self):
                return self.get_url_for_this_object('detail')

        class CrudListView(BaseMixin, ListView):
            model = self.model
            title = model._meta.verbose_name_plural

        class CrudCreateView(BaseMixin, FormMessagesMixin, CreateView):
            model = self.model
            form_class = model_form
            title = _('Adicionar %(model_name)s') % {
                'model_name': self.model._meta.verbose_name}
            form_valid_message = _('Registro criado com sucesso!')
            form_invalid_message = make_form_invalid_message(
                _('O registro não foi criado.'))

            def get_success_url(self):
                return self.detail_url

        class CrudDetailView(BaseMixin, DetailView):
            model = self.model

        class CrudUpdateView(BaseMixin, FormMessagesMixin, UpdateView):
            model = self.model
            form_class = model_form
            form_valid_message = _('Mudanças salvas com sucesso!')
            form_invalid_message = make_form_invalid_message(
                _('Suas mudanças não foram salvas.'))

            def get_success_url(self):
                return self.detail_url

        class CrudDeleteView(BaseMixin, FormMessagesMixin, DeleteView):
            model = self.model
            form_valid_message = _('Registro excluído com sucesso!')
            form_invalid_message = make_form_invalid_message(
                _('O registro não foi excluído.'))

            def get_success_url(self):
                return self.list_url

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
