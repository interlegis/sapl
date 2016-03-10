from braces.views import FormMessagesMixin
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from crispy_layout_mixin import CrispyLayoutFormMixin, get_field_display


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


class BaseCrudMixin(CrispyLayoutFormMixin):

    @property
    def namespace(self):
        return self.model._meta.model_name

    def resolve_url(self, url_name, args=None):
        return reverse('%s:%s' % (self.namespace, url_name), args=args)

    @property
    def list_url(self):
        return self.resolve_url('list')

    @property
    def create_url(self):
        return self.resolve_url('create')

    @property
    def detail_url(self):
        return self.resolve_url('detail', args=(self.object.id,))

    @property
    def update_url(self):
        return self.resolve_url('update', args=(self.object.id,))

    @property
    def delete_url(self):
        return self.resolve_url('delete', args=(self.object.id,))

    def get_template_names(self):
        names = super(BaseCrudMixin, self).get_template_names()
        names.append("crud/%s.html" %
                     self.template_name_suffix.lstrip('_'))
        return names

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural


class CrudListMixin():

    paginate_by = 10
    no_entries_msg = _('Nenhum registro encontrado.')

    def _as_row(self, obj):
        return [
            (get_field_display(obj, name)[1], obj.pk if i == 0 else None)
            for i, name in enumerate(self.list_field_names)]

    def get_context_data(self, **kwargs):
        context = super(CrudListMixin, self).get_context_data(**kwargs)
        context.setdefault('title', self.verbose_name_plural)

        # pagination
        page_obj = context['page_obj']
        paginator = context['paginator']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        # rows
        object_list = context['object_list']
        context['rows'] = [self._as_row(obj) for obj in object_list]

        context['headers'] = [
            self.model._meta.get_field(fieldname).verbose_name
            for fieldname in self.list_field_names]
        context['NO_ENTRIES_MSG'] = self.no_entries_msg

        return context


def make_form_invalid_message(msg):
    return '%s %s' % (_('Formulário inválido.'), msg)


class CrudCreateMixin(FormMessagesMixin):

    form_valid_message = _('Registro criado com sucesso!')
    form_invalid_message = make_form_invalid_message(
        _('O registro não foi criado.'))

    @property
    def cancel_url(self):
        return self.list_url

    def get_success_url(self):
        return self.detail_url

    def get_context_data(self, **kwargs):
        kwargs.setdefault('title', _('Adicionar %(verbose_name)s') % {
            'verbose_name': self.verbose_name})
        return super(CrudCreateMixin, self).get_context_data(**kwargs)


class CrudDetailMixin():
    pass


class CrudUpdateMixin(FormMessagesMixin):

    form_valid_message = _('Registro alterado com sucesso!')
    form_invalid_message = make_form_invalid_message(
        _('Suas alterações não foram salvas.'))

    @property
    def cancel_url(self):
        return self.detail_url

    def get_success_url(self):
        return self.detail_url


class CrudDeleteMixin(FormMessagesMixin):

    form_valid_message = _('Registro excluído com sucesso!')
    form_invalid_message = make_form_invalid_message(
        _('O registro não foi excluído.'))

    @property
    def cancel_url(self):
        return self.detail_url

    def get_success_url(self):
        return self.list_url


class Crud:

    def __init__(self, model, help_path,
                 base_mixin=BaseCrudMixin,
                 list_mixin=CrudListMixin,
                 create_mixin=CrudCreateMixin,
                 detail_mixin=CrudDetailMixin,
                 update_mixin=CrudUpdateMixin,
                 delete_mixin=CrudDeleteMixin):

        class CrudMixin(base_mixin):
            pass
        CrudMixin.model = model
        CrudMixin.help_path = help_path

        class CrudListView(CrudMixin, list_mixin, ListView):
            pass

        class CrudCreateView(CrudMixin, create_mixin, CreateView):
            pass

        class CrudDetailView(CrudMixin, detail_mixin, DetailView):
            pass

        class CrudUpdateView(CrudMixin, update_mixin, UpdateView):
            pass

        class CrudDeleteView(CrudMixin, delete_mixin, DeleteView):
            pass

        self.urlpatterns = [
            url(r'^$', CrudListView.as_view(), name='list'),
            url(r'^create$', CrudCreateView.as_view(), name='create'),
            url(r'^(?P<pk>\d+)$', CrudDetailView.as_view(), name='detail'),
            url(r'^(?P<pk>\d+)/edit$',
                CrudUpdateView.as_view(), name='update'),
            url(r'^(?P<pk>\d+)/delete$',
                CrudDeleteView.as_view(), name='delete'),
        ]

        self.namespace = CrudMixin().namespace
        self.urls = self.urlpatterns, self.namespace, self.namespace

        # FIXME Refatorar código que precisa desse atributo e remover
        self.CrudDetailView = CrudDetailView
