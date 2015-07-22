from braces.views import FormMessagesMixin
from crispy_forms.helper import FormHelper
from django import forms
from django.conf.urls import url
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView, DetailView)

from sapl.layout import SaplFormLayout


class Crud(object):
    pass


def build_crud(model, *layout):
    crud = Crud()
    crud.model = model
    crud.namespace = model._meta.model_name

    class CrispyForm(forms.ModelForm):

        class Meta:
            model = crud.model
            exclude = []

        def __init__(self, *args, **kwargs):
            super(CrispyForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.layout = SaplFormLayout(*layout)

    crud.model_form = CrispyForm

    def in_namespace(url_name):
        return '%s:%s' % (crud.namespace, url_name)

    def make_form_invalid_message(msg):
        return '%s %s' % (_('Formulário inválido.'), msg)

    class BaseMixin(object):
        model = crud.model

        verbose_name = crud.model._meta.verbose_name
        verbose_name_plural = crud.model._meta.verbose_name_plural

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
            return self.get_url_for_this_object('update')

        @property
        def delete_url(self):
            return self.get_url_for_this_object('delete')

    class CrudListView(BaseMixin, ListView):
        title = BaseMixin.verbose_name_plural

    class CrudCreateView(BaseMixin, FormMessagesMixin, CreateView):
        form_class = crud.model_form
        title = _('Adicionar %(verbose_name)s') % {
            'verbose_name': BaseMixin.verbose_name}
        form_valid_message = _('Registro criado com sucesso!')
        form_invalid_message = make_form_invalid_message(
            _('O registro não foi criado.'))

        def get_success_url(self):
            return self.detail_url

    class CrudDetailView(BaseMixin, DetailView):

        @property
        def title(self):
            return self.get_object()

    class CrudUpdateView(BaseMixin, FormMessagesMixin, UpdateView):
        form_class = crud.model_form
        form_valid_message = _('Registro alterado com sucesso!')
        form_invalid_message = make_form_invalid_message(
            _('Suas alterações não foram salvas.'))

        @property
        def title(self):
            return self.get_object()

        def get_success_url(self):
            return self.detail_url

    class CrudDeleteView(BaseMixin, FormMessagesMixin, DeleteView):
        form_valid_message = _('Registro excluído com sucesso!')
        form_invalid_message = make_form_invalid_message(
            _('O registro não foi excluído.'))

        def get_success_url(self):
            return self.list_url

    crud.CrudListView = CrudListView
    crud.CrudCreateView = CrudCreateView
    crud.CrudDetailView = CrudDetailView
    crud.CrudUpdateView = CrudUpdateView
    crud.CrudDeleteView = CrudDeleteView

    # XXX transform into a property of Crud to enable override
    crud.urls = [
        url(r'^$', CrudListView.as_view(), name='list'),
        url(r'^create$', CrudCreateView.as_view(), name='create'),
        url(r'^(?P<pk>\d+)$', CrudDetailView.as_view(), name='detail'),
        url(r'^(?P<pk>\d+)/edit$',
            CrudUpdateView.as_view(), name='update'),
        url(r'^(?P<pk>\d+)/delete$',
            CrudDeleteView.as_view(), name='delete'),
    ], crud.namespace, crud.namespace

    return crud
