from braces.views import FormMessagesMixin
from crispy_forms.helper import FormHelper
from datetime import datetime
from django import forms
from django.conf.urls import url
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from sapl.layout import SaplFormLayout

NO_ENTRIES_MSG = _('Não existem registros')


def from_to(start, end):
    return list(range(start, end + 1))


def make_pagination(index, num_pages):
    '''Make a list of adjacent page ranges interspersed with "None"s

    The list starts with [1, 2] and end with [num_pages-1, num_pages].
    The list includes [index-1, index, index+1]
    "None"s separate those ranges and mean ellipsis (...)

    Example:  [1, 2, None, 10, 11, 12, None, 29, 30]
    '''

    PAGINATION_LENGTH = 10
    if num_pages <= PAGINATION_LENGTH:
        return from_to(1, num_pages)
    else:
        if index - 1 <= 5:
            tail = [num_pages - 1, num_pages]
            head = from_to(1, PAGINATION_LENGTH - 3)
        else:
            if index + 1 >= num_pages - 3:
                tail = from_to(index - 1, num_pages)
            else:
                tail = [index - 1, index, index + 1,
                        None, num_pages - 1, num_pages]
            head = from_to(1, PAGINATION_LENGTH - len(tail) - 1)
        return head + [None] + tail


def get_field_display(obj, fieldname):
    field = obj._meta.get_field(fieldname)
    verbose_name = str(field.verbose_name)
    if field.choices:
        value = getattr(obj, 'get_%s_display' % fieldname)()
    else:
        value = getattr(obj, fieldname)
    if value is None:
        display = ''
    elif 'date' in str(type(value)):
        display = value.strftime("%d/%m/%Y")
    else:
        display = str(value)

    return verbose_name, display


class Crud(object):
    pass


def build_crud(model, help_path, layout):
    crud = Crud()
    crud.model = model
    crud.help_path = help_path
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
        help_path = crud.help_path  # FIXME

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

        def get_template_names(self):
            names = super(BaseMixin, self).get_template_names()
            names.append("crud/%s.html" %
                         self.template_name_suffix.lstrip('_'))
            return names

    class CrudListView(BaseMixin, ListView):
        title = BaseMixin.verbose_name_plural
        paginate_by = 10
        no_entries_msg = NO_ENTRIES_MSG

        @cached_property
        def field_names(self):
            '''The list of field names to display on table

            This base implementation returns the field names
            in the first fieldset of the layout.
            '''
            rows = layout[0][1:]
            return [fieldname for row in rows for fieldname, __ in row]

        def get_rows(self, object_list):
            return [[(get_field_display(obj, name)[1],
                      obj.pk if i == 0 else None)
                     for i, name in enumerate(self.field_names)]
                    for obj in object_list
                    ]

        def get_context_data(self, **kwargs):
            context = super(CrudListView, self).get_context_data(**kwargs)
            paginator = context['paginator']
            page_obj = context['page_obj']
            context['page_range'] = make_pagination(
                page_obj.number, paginator.num_pages)
            object_list = context['object_list']
            context['headers'] = [
                self.model._meta.get_field(fieldname).verbose_name
                for fieldname in self.field_names]
            context['rows'] = self.get_rows(object_list)
            context['NO_ENTRIES_MSG'] = NO_ENTRIES_MSG
            return context

    class CrudCreateView(BaseMixin, FormMessagesMixin, CreateView):
        form_class = crud.model_form
        title = _('Adicionar %(verbose_name)s') % {
            'verbose_name': BaseMixin.verbose_name}
        form_valid_message = _('Registro criado com sucesso!')
        form_invalid_message = make_form_invalid_message(
            _('O registro não foi criado.'))
        cancel_url = BaseMixin.list_url

        def get_success_url(self):
            return self.detail_url

    class CrudDetailView(BaseMixin, DetailView):

        @property
        def title(self):
            return self.get_object()

        def get_column(self, fieldname, span):
            obj = self.get_object()
            verbose_name, text = get_field_display(obj, fieldname)
            return {
                'id': fieldname,
                'span': span,
                'verbose_name': verbose_name,
                'text': text,
            }

        @property
        def fieldsets(self):
            return [
                {'legend': legend,
                 'rows': [[self.get_column(fieldname, span)
                           for fieldname, span in row]
                          for row in rows]
                 } for legend, *rows in layout]

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

        def cancel_url(self):
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
    crud.urlpatterns = [
        url(r'^$', CrudListView.as_view(), name='list'),
        url(r'^create$', CrudCreateView.as_view(), name='create'),
        url(r'^(?P<pk>\d+)$', CrudDetailView.as_view(), name='detail'),
        url(r'^(?P<pk>\d+)/edit$',
            CrudUpdateView.as_view(), name='update'),
        url(r'^(?P<pk>\d+)/delete$',
            CrudDeleteView.as_view(), name='delete'),
    ]
    crud.urls = crud.urlpatterns, crud.namespace, crud.namespace

    return crud
