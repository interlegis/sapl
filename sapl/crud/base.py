import logging

from braces.views import FormMessagesMixin
from compressor.utils.decorators import cached_property
from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.conf.urls import url
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.urlresolvers import reverse
from django.db import models
from django.http.response import Http404
from django.utils.decorators import classonlymethod
from django.utils.encoding import force_text
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.views.generic.base import ContextMixin
from django.views.generic.list import MultipleObjectMixin

from sapl.crispy_layout_mixin import CrispyLayoutFormMixin, get_field_display
from sapl.utils import normalize


logger = logging.getLogger(__name__)

ACTION_LIST, ACTION_CREATE, ACTION_DETAIL, ACTION_UPDATE, ACTION_DELETE = \
    'list', 'create', 'detail', 'update', 'delete'

# RP - Radical das permissões para "..."
RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE =\
    '.list_', '.detail_', '.add_', '.change_', '.delete_',


def _form_invalid_message(msg):
    return '%s %s' % (_('Formulário inválido.'), msg)

FORM_MESSAGES = {ACTION_CREATE: (_('Registro criado com sucesso!'),
                                 _('O registro não foi criado.')),
                 ACTION_UPDATE: (_('Registro alterado com sucesso!'),
                                 _('Suas alterações não foram salvas.')),
                 ACTION_DELETE: (_('Registro excluído com sucesso!'),
                                 _('O registro não foi excluído.'))}
FORM_MESSAGES = {k: (a, _form_invalid_message(b))
                 for k, (a, b) in FORM_MESSAGES.items()}


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

"""
variáveis do crud:
    help_path
    container_field
    container_field_set
    is_m2m
    model
    model_set
    form_search_class -> depende de o model relativo implementar SearchMixin
    list_field_names
    list_field_names_set -> lista reversa em details
    permission_required -> este atributo ser vazio não nulo torna a view publ
    layout_key_set
    layout_key
    ordered_list = False desativa os clicks e controles de ord da listagem
    parent_field = parentesco reverso separado por '__'
    namespace
"""


class SearchMixin(models.Model):

    search = models.TextField(blank=True, default='')

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, auto_update_search=True):

        if auto_update_search and hasattr(self, 'fields_search'):
            search = ''
            for str_field in self.fields_search:
                fields = str_field.split('__')
                if len(fields) == 1:
                    try:
                        search += str(getattr(self, str_field)) + ' '
                    except:
                        pass
                else:
                    _self = self
                    for field in fields:
                        _self = getattr(_self, field)
                    search += str(_self) + ' '
            self.search = search
        self.search = normalize(self.search)

        return super(SearchMixin, self).save(
            force_insert=force_insert, force_update=force_update,
            using=using, update_fields=update_fields)


class ListWithSearchForm(forms.Form):
    q = forms.CharField(required=False, label='',
                        widget=forms.TextInput(
                            attrs={'type': 'search'}))

    o = forms.CharField(required=False, label='',
                        widget=forms.HiddenInput())

    class Meta:
        fields = ['q', 'o']

    def __init__(self, *args, **kwargs):
        super(ListWithSearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.form_class = 'form-inline'
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Field('o'),
            FieldWithButtons(
                Field('q',
                      placeholder=_('Filtrar Lista'),
                      css_class='input-lg'),
                StrictButton(
                    _('Filtrar'), css_class='btn-default btn-lg',
                    type='submit'))
        )


class PermissionRequiredForAppCrudMixin(PermissionRequiredMixin):

    def has_permission(self):
        apps = self.app_label
        if isinstance(apps, str):
            apps = apps,
        # papp_label vazio dará acesso geral
        for app in apps:
            if not self.request.user.has_module_perms(app):
                return False
        return True


class PermissionRequiredContainerCrudMixin(PermissionRequiredMixin):

    def has_permission(self):
        perms = self.get_permission_required()
        # Torna a view pública se não possuir conteudo
        # no atributo permission_required
        return self.request.user.has_perms(perms) if len(perms) else True

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()

        if 'pk' in kwargs:
            params = {'pk': kwargs['pk']}

            if self.container_field:
                params[self.container_field] = request.user.pk

                if not self.model.objects.filter(**params).exists():
                    raise Http404()

        return super(PermissionRequiredMixin, self).dispatch(
            request, *args, **kwargs)

    @cached_property
    def container_field(self):
        if hasattr(self, 'crud') and not hasattr(self.crud, 'container_field'):
            self.crud.container_field = ''
        if hasattr(self, 'crud'):
            return self.crud.container_field

    @cached_property
    def container_field_set(self):
        if hasattr(self, 'crud') and\
                not hasattr(self.crud, 'container_field_set'):
            self.crud.container_field_set = ''
        if hasattr(self, 'crud'):
            return self.crud.container_field_set

    @cached_property
    def is_contained(self):
        return self.container_field_set or self.container_field


class CrudBaseMixin(CrispyLayoutFormMixin):

    def __init__(self, **kwargs):
        super(CrudBaseMixin, self).__init__(**kwargs)
        obj = self.crud if hasattr(self, 'crud') else self
        self.app_label = obj.model._meta.app_label
        self.model_name = obj.model._meta.model_name

        if hasattr(obj, 'model_set') and obj.model_set:
            self.app_label_set = getattr(
                obj.model, obj.model_set).field.model._meta.app_label
            self.model_name_set = getattr(
                obj.model, obj.model_set).field.model._meta.model_name

        if hasattr(self, 'permission_required') and self.permission_required:
            if hasattr(obj, 'public'):
                self.permission_required = list(
                    set(self.permission_required) - set(obj.public))

            self.permission_required = tuple((
                self.permission(pr) for pr in self.permission_required))

    @classmethod
    def url_name(cls, suffix):
        return '%s_%s' % (cls.model._meta.model_name, suffix)

    def url_name_set(self, suffix):
        obj = self.crud if hasattr(self, 'crud') else self
        return '%s_%s' % (getattr(obj.model, obj.model_set
                                  ).field.model._meta.model_name, suffix)

    def permission(self, rad):
        return '%s%s%s' % (self.app_label if rad.endswith('_') else '',
                           rad,
                           self.model_name if rad.endswith('_') else '')

    def permission_set(self, rad):
        return '%s%s%s' % (self.app_label_set if rad.endswith('_') else '',
                           rad,
                           self.model_name_set if rad.endswith('_') else '')

    def resolve_url(self, suffix, args=None):
        namespace = self.model._meta.app_config.name
        return reverse('%s:%s' % (namespace, self.url_name(suffix)),
                       args=args)

    def resolve_url_set(self, suffix, args=None):
        obj = self.crud if hasattr(self, 'crud') else self
        namespace = getattr(
            obj.model, obj.model_set).field.model._meta.app_config.name
        return reverse('%s:%s' % (namespace, self.url_name_set(suffix)),
                       args=args)

    @property
    def ordered_list(self):
        return True

    @property
    def list_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if not obj.ListView.permission_required:
            return self.resolve_url(ACTION_LIST)
        else:
            return self.resolve_url(
                ACTION_LIST) if self.request.user.has_perm(
                self.permission(RP_LIST)) else ''

    @property
    def create_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if not obj.CreateView.permission_required:
            return self.resolve_url(ACTION_CREATE)
        else:
            return self.resolve_url(
                ACTION_CREATE) if self.request.user.has_perm(
                self.permission(RP_ADD)) else ''

    @property
    def detail_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if not obj.DetailView.permission_required:
            return self.resolve_url(ACTION_DETAIL, args=(self.object.id,))
        else:
            return self.resolve_url(ACTION_DETAIL, args=(self.object.id,))\
                if self.request.user.has_perm(
                    self.permission(RP_DETAIL)) else ''

    @property
    def update_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if not obj.UpdateView.permission_required:
            return self.resolve_url(ACTION_UPDATE, args=(self.object.id,))
        else:
            return self.resolve_url(ACTION_UPDATE, args=(self.object.id,))\
                if self.request.user.has_perm(
                    self.permission(RP_CHANGE)) else ''

    @property
    def delete_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if not obj.DeleteView.permission_required:
            return self.resolve_url(ACTION_DELETE, args=(self.object.id,))
        else:
            return self.resolve_url(ACTION_DELETE, args=(self.object.id,))\
                if self.request.user.has_perm(
                    self.permission(RP_DELETE)) else ''

    def get_template_names(self):
        names = super(CrudBaseMixin, self).get_template_names()
        names.append("crud/%s.html" %
                     self.template_name_suffix.lstrip('_'))
        return names

    @property
    def verbose_name_set(self):
        obj = self.crud if hasattr(self, 'crud') else self
        return getattr(obj.model, obj.model_set).field.model._meta.verbose_name

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural


class CrudListView(PermissionRequiredContainerCrudMixin, ListView):
    permission_required = (RP_LIST, )

    @classmethod
    def get_url_regex(cls):
        return r'^$'
    paginate_by = 10
    no_entries_msg = _('Nenhum registro encontrado.')

    def get_rows(self, object_list):
        return [self._as_row(obj) for obj in object_list]

    def get_headers(self):
        """
        Transforma o headers de fields de list_field_names
        para junção de fields via tuplas.
        list_field_names pode ser construido como
        list_field_names=('nome', 'endereco', ('telefone', sexo'), 'dat_nasc')
        ou ainda:
          list_field_names = ['composicao__comissao__nome', 'cargo__nome', (
          'composicao__periodo__data_inicio', 'composicao__periodo__data_fim')]
        """
        r = []
        for fieldname in self.list_field_names:
            if not isinstance(fieldname, tuple):
                fieldname = fieldname,
            s = []
            for fn in fieldname:
                m = self.model
                fn = fn.split('__')
                for f in fn:
                    f = m._meta.get_field(f)
                    if hasattr(f, 'related_model') and f.related_model:
                        m = f.related_model
                if m == self.model:
                    s.append(force_text(f.verbose_name))
                else:
                    s.append(force_text(m._meta.verbose_name))
            s = ' / '.join(s)
            r.append(s)
        return r

    def _as_row(self, obj):
        """
        FIXME: Refatorar função para capturar url correta em caso de uso de
        campos foreignkey. getHeaders já faz isso para construir o título.
        falta fazer com esta função
        """
        r = []
        for i, name in enumerate(self.list_field_names):
            url = self.resolve_url(
                ACTION_DETAIL, args=(obj.id,)) if i == 0 else None

            """Caso o crud list seja para uma relação ManyToManyField"""
            if url and hasattr(self, 'crud') and\
                    hasattr(self.crud, 'is_m2m') and self.crud.is_m2m:
                url = url + ('?pkk=' + self.kwargs['pk']
                             if 'pk' in self.kwargs else '')

            """ se elemento de list_field_name for uma tupla, constrói a
            informação com ' - ' se os campos forem simples,
            ou com <br> se for m2m """
            if isinstance(name, tuple):
                s = ''
                for j, n in enumerate(name):
                    ss = get_field_display(obj, n)[1]
                    ss = (
                        ('<br>' if '<ul>' in ss else ' - ') + ss)\
                        if ss and j != 0 and s else ss
                    s += ss
                r.append((s, url))
            else:
                r.append((get_field_display(obj, name)[1], url))
        return r

    def get_context_data(self, **kwargs):
        """ Relevante se na implmentação do crud list, for informado
        um formulário de pesquisa herdado ou o próprio ListWithSearchForm.
        Só pode ser usado se o model relativo herdar de SearchMixin"""
        if hasattr(self, 'form_search_class'):
            q = str(self.request.GET.get('q'))\
                if 'q' in self.request.GET else ''

            o = self.request.GET['o'] if 'o' in self.request.GET else '1'

            if 'form' not in kwargs:
                initial = self.get_initial() if hasattr(
                    self, 'get_initial') else {}
                initial.update({'q': q, 'o': o})
                kwargs['form'] = self.form_search_class(
                    initial=initial)

        count = self.object_list.count()
        context = super().get_context_data(**kwargs)
        context.setdefault('title', self.verbose_name_plural)
        context['count'] = count

        # pagination
        if self.paginate_by:
            page_obj = context['page_obj']
            paginator = context['paginator']
            context['page_range'] = make_pagination(
                page_obj.number, paginator.num_pages)

        # rows
        object_list = context['object_list']
        context['headers'] = self.get_headers()
        context['rows'] = self.get_rows(object_list)

        context['NO_ENTRIES_MSG'] = self.no_entries_msg

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = (
            '&' + qr.urlencode()) if len(qr) > 0 else ''

        if self.ordered_list:
            if 'o' in qr:
                del qr['o']
            context['ordering_url'] = (
                '&' + qr.urlencode()) if len(qr) > 0 else ''
        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        # form_search_class
        # só pode ser usado em models que herdam de SearchMixin
        if hasattr(self, 'form_search_class'):
            request = self.request
            if request.GET.get('q') is not None:
                query = normalize(str(request.GET.get('q')))

                query = query.split(' ')
                if query:
                    q = models.Q()
                    for item in query:
                        if not item:
                            continue
                        q = q & models.Q(search__icontains=item)

                    if q:
                        queryset = queryset.filter(q)

        if self.ordered_list:
            list_field_names = self.list_field_names
            o = '1'
            desc = ''
            if 'o' in self.request.GET:
                o = self.request.GET['o']
                desc = '-' if o.startswith('-') else ''

                # Constroi a ordenação da listagem com base no que o usuário
                # clicar
                try:
                    fields_for_ordering = list_field_names[
                        (abs(int(o)) - 1) % len(list_field_names)]

                    if isinstance(fields_for_ordering, str):
                        fields_for_ordering = [fields_for_ordering, ]

                    ordering = ()
                    model = self.model
                    for fo in fields_for_ordering:

                        fm = None
                        try:
                            fm = model._meta.get_field(fo)
                        except:
                            pass

                        if fm and hasattr(fm, 'related_model')\
                                and fm.related_model:
                            rmo = fm.related_model._meta.ordering
                            if rmo:
                                rmo = rmo[0]
                                if not isinstance(rmo, str):
                                    rmo = rmo[0]
                                fo = '%s__%s' % (fo, rmo)

                        fo = desc + fo
                        ordering += (fo,)

                    model = self.model
                    model_ordering = model._meta.ordering
                    if model_ordering:
                        if isinstance(model_ordering, str):
                            model_ordering = (model_ordering,)
                        for mo in model_ordering:
                            if mo not in ordering:
                                ordering = ordering + (mo, )
                    queryset = queryset.order_by(*ordering)

                    # print(ordering)
                except Exception as e:
                    logger.error(string_concat(_(
                        'ERRO: construção da tupla de ordenação.'), str(e)))

        # print(queryset.query)
        if not self.request.user.is_authenticated():
            return queryset

        if self.container_field:
            params = {}
            params[self.container_field] = self.request.user.pk
            queryset = queryset.filter(**params)

        return queryset


class CrudCreateView(PermissionRequiredContainerCrudMixin,
                     FormMessagesMixin, CreateView):
    permission_required = (RP_ADD, )

    @classmethod
    def get_url_regex(cls):
        return r'^create$'

    form_valid_message, form_invalid_message = FORM_MESSAGES[ACTION_CREATE]

    @property
    def cancel_url(self):
        return self.list_url

    def get_success_url(self):
        return self.detail_url

    def get_context_data(self, **kwargs):
        kwargs.setdefault('title', _('Adicionar %(verbose_name)s') % {
            'verbose_name': self.verbose_name})
        return super(CrudCreateView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        try:
            self.object.owner = self.request.user
            self.object.modifier = self.request.user
        except:
            pass

        if self.container_field:
            container = self.container_field.split('__')

            if len(container) > 1:
                container_model = getattr(
                    self.model, container[0]).field.related_model

                params = {}
                params['__'.join(
                    container[1:])] = self.request.user.pk

                if 'pk' in self.kwargs:
                    params['pk'] = self.kwargs['pk']

                container_data = container_model.objects.filter(
                    **params).first()

                if not container_data:
                    raise Exception(
                        _('Não é permitido adicionar um registro '
                          'sem estar em um Container'))

                if hasattr(self, 'crud') and\
                        hasattr(self.crud, 'is_m2m') and self.crud.is_m2m:
                    setattr(
                        self.object, container[1], getattr(
                            container_data, container[1]))
                    response = super().form_valid(form)
                    getattr(self.object, container[0]).add(container_data)
                    return response
                else:
                    setattr(self.object, container[0], container_data)

        return super().form_valid(form)


class CrudDetailView(PermissionRequiredContainerCrudMixin,
                     DetailView, MultipleObjectMixin):

    permission_required = (RP_DETAIL, )
    no_entries_msg = _('Nenhum registro Associado.')
    paginate_by = 10

    @classmethod
    def get_url_regex(cls):
        return r'^(?P<pk>\d+)$'

    def get_rows(self, object_list):
        return [self._as_row(obj) for obj in object_list]

    def get_headers(self):
        if not self.object_list:
            return []
        try:
            obj = self.crud if hasattr(self, 'crud') else self
            return [
                (getattr(
                    self.object, obj.model_set).model._meta.get_field(
                    fieldname).verbose_name
                 if hasattr(self.object, fieldname) else
                    getattr(
                    self.object, obj.model_set).model._meta.get_field(
                    fieldname).related_model._meta.verbose_name_plural)
                for fieldname in self.list_field_names_set]
        except:
            obj = self.crud if hasattr(self, 'crud') else self
            return [getattr(
                self.object,
                obj.model_set).model._meta.verbose_name_plural]

    def url_model_set_name(self, suffix):
        return '%s_%s' % (
            getattr(self.object,
                    self.crud.model_set).model._meta.model_name,
            suffix)

    def resolve_model_set_url(self, suffix, args=None):
        obj = self.crud if hasattr(self, 'crud') else self
        namespace = getattr(
            self.object, obj.model_set).model._meta.app_config.name
        return reverse('%s:%s' % (
            namespace, self.url_model_set_name(suffix)),
            args=args)

    def _as_row(self, obj):
        try:
            return [(
                get_field_display(obj, name)[1],
                self.resolve_model_set_url(ACTION_DETAIL, args=(obj.id,))
                if i == 0 else None)
                for i, name in enumerate(self.list_field_names_set)]
        except:
            return [(
                getattr(obj, name),
                self.resolve_model_set_url(ACTION_DETAIL, args=(obj.id,))
                if i == 0 else None)
                for i, name in enumerate(self.list_field_names_set)]

    def get_object(self, queryset=None):
        if hasattr(self, 'object'):
            return self.object
        return DetailView.get_object(self, queryset=queryset)

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.model.objects.get(pk=kwargs.get('pk'))
        except:
            raise Http404
        obj = self.crud if hasattr(self, 'crud') else self
        if hasattr(obj, 'model_set') and obj.model_set:
            self.object_list = self.get_queryset()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if hasattr(obj, 'model_set') and obj.model_set:
            queryset = getattr(self.object, obj.model_set).all()
        else:
            queryset = super().get_queryset()

        if not self.request.user.is_authenticated():
            return queryset

        if self.container_field_set:
            params = {}
            params[self.container_field_set] = self.request.user.pk
            return queryset.filter(**params)

        return queryset

    def get_context_data(self, **kwargs):
        obj = self.crud if hasattr(self, 'crud') else self
        if hasattr(obj, 'model_set') and obj.model_set:
            count = self.object_list.count()
            context = MultipleObjectMixin.get_context_data(self, **kwargs)
            context['count'] = count
            if self.paginate_by:
                page_obj = context['page_obj']
                paginator = context['paginator']
                context['page_range'] = make_pagination(
                    page_obj.number, paginator.num_pages)

            # rows
            object_list = context['object_list']
            context['headers'] = self.get_headers()
            context['rows'] = self.get_rows(object_list)

            context['NO_ENTRIES_MSG'] = self.no_entries_msg
        else:
            context = ContextMixin.get_context_data(self, **kwargs)
            if self.object:
                context['object'] = self.object
                context_object_name = self.get_context_object_name(
                    self.object)
                if context_object_name:
                    context[context_object_name] = self.object
            context.update(kwargs)

        return context

    @property
    def model_set_verbose_name(self):
        obj = self.crud if hasattr(self, 'crud') else self
        return getattr(
            self.object,
            obj.model_set).model._meta.verbose_name

    @property
    def model_set_verbose_name_plural(self):
        obj = self.crud if hasattr(self, 'crud') else self
        return getattr(
            self.object,
            obj.model_set).model._meta.verbose_name_plural


class CrudUpdateView(PermissionRequiredContainerCrudMixin,
                     FormMessagesMixin, UpdateView):
    permission_required = (RP_CHANGE, )

    def form_valid(self, form):
        self.object = form.save(commit=False)
        try:
            self.object.modifier = self.request.user
        except:
            pass

        return super().form_valid(form)

    @classmethod
    def get_url_regex(cls):
        return r'^(?P<pk>\d+)/edit$'

    form_valid_message, form_invalid_message = FORM_MESSAGES[ACTION_UPDATE]

    @property
    def cancel_url(self):
        return self.detail_url

    def get_success_url(self):
        return self.detail_url


class CrudDeleteView(PermissionRequiredContainerCrudMixin,
                     FormMessagesMixin, DeleteView):
    permission_required = (RP_DELETE, )

    @classmethod
    def get_url_regex(cls):
        return r'^(?P<pk>\d+)/delete$'

    form_valid_message, form_invalid_message = FORM_MESSAGES[ACTION_DELETE]

    @property
    def cancel_url(self):
        return self.detail_url

    def get_success_url(self):
        return self.list_url


class Crud:
    BaseMixin = CrudBaseMixin
    ListView = CrudListView
    CreateView = CrudCreateView
    DetailView = CrudDetailView
    UpdateView = CrudUpdateView
    DeleteView = CrudDeleteView
    help_path = ''

    class PublicMixin:
        permission_required = []

    @classonlymethod
    def get_urls(cls):

        def _add_base(view):
            if view:
                class CrudViewWithBase(cls.BaseMixin, view):
                    model = cls.model
                    help_path = cls.help_path
                    crud = cls
                CrudViewWithBase.__name__ = view.__name__
                return CrudViewWithBase

        CrudListView = _add_base(cls.ListView)
        CrudCreateView = _add_base(cls.CreateView)
        CrudDetailView = _add_base(cls.DetailView)
        CrudUpdateView = _add_base(cls.UpdateView)
        CrudDeleteView = _add_base(cls.DeleteView)

        cruds_base = [
            (CrudListView.get_url_regex()
             if CrudListView else None, CrudListView, ACTION_LIST),
            (CrudCreateView.get_url_regex()
             if CrudCreateView else None, CrudCreateView, ACTION_CREATE),
            (CrudDetailView.get_url_regex()
             if CrudDetailView else None, CrudDetailView, ACTION_DETAIL),
            (CrudUpdateView.get_url_regex()
             if CrudUpdateView else None, CrudUpdateView, ACTION_UPDATE),
            (CrudDeleteView.get_url_regex()
             if CrudDeleteView else None, CrudDeleteView, ACTION_DELETE)]

        cruds = []
        for crud in cruds_base:
            if crud[0]:
                cruds.append(crud)

        return [url(regex, view.as_view(), name=view.url_name(suffix))
                for regex, view, suffix in cruds]

    @classonlymethod
    def build(cls, _model, _help_path, _model_set=None, list_field_names=[]):

        def create_class(_list_field_names):
            class ModelCrud(cls):
                model = _model
                model_set = _model_set
                help_path = _help_path
                list_field_names = _list_field_names
            return ModelCrud

        ModelCrud = create_class(list_field_names)
        ModelCrud.__name__ = '%sCrud' % _model.__name__
        return ModelCrud


class CrudAux(Crud):

    class BaseMixin(Crud.BaseMixin):
        permission_required = ('base.view_tabelas_auxiliares',)
        subnav_template_name = None

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = self.subnav_template_name
            return context

    @classonlymethod
    def build(cls, _model, _help_path, _model_set=None, list_field_names=[]):

        ModelCrud = Crud.build(
            _model, _help_path, _model_set, list_field_names)

        class ModelCrudAux(ModelCrud):
            BaseMixin = CrudAux.BaseMixin

        return ModelCrudAux


class MasterDetailCrud(Crud):
    is_m2m = False

    class BaseMixin(Crud.BaseMixin):

        @property
        def list_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.ListView:
                return ''
            return self.resolve_url(ACTION_LIST, args=(self.kwargs['pk'],))\
                if self.request.user.has_perm(self.permission(RP_LIST)) else ''

        @property
        def create_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.CreateView:
                return ''
            return self.resolve_url(ACTION_CREATE, args=(self.kwargs['pk'],))\
                if self.request.user.has_perm(self.permission(RP_ADD)) else ''

        @property
        def detail_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.DetailView:
                return ''
            pkk = self.request.GET['pkk'] if 'pkk' in self.request.GET else ''
            return (super().detail_url + (('?pkk=' + pkk) if pkk else ''))\
                if self.request.user.has_perm(
                    self.permission(RP_DETAIL)) else ''

        @property
        def update_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.UpdateView:
                return ''
            pkk = self.request.GET['pkk'] if 'pkk' in self.request.GET else ''
            return (super().update_url + (('?pkk=' + pkk) if pkk else ''))\
                if self.request.user.has_perm(
                    self.permission(RP_CHANGE)) else ''

        @property
        def delete_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.DeleteView:
                return ''
            return super().delete_url\
                if self.request.user.has_perm(
                    self.permission(RP_DELETE)) else ''

        def get_context_data(self, **kwargs):
            obj = self.crud if hasattr(self, 'crud') else self
            self.object = getattr(self, 'object', None)
            parent_object = None
            if self.object:
                if '__' in obj.parent_field:
                    fields = obj.parent_field.split('__')
                    parent_object = self.object
                    for field in fields:
                        parent_object = getattr(parent_object, field)
                else:
                    parent_object = getattr(self.object, obj.parent_field)
                if not isinstance(parent_object, models.Model):
                    if parent_object.count() > 1:
                        if 'pkk' not in self.request.GET:
                            raise Http404
                        root_pk = self.request.GET['pkk']
                        parent_object = parent_object.filter(id=root_pk)

                    parent_object = parent_object.first()

                    if not parent_object:
                        raise Http404
                root_pk = parent_object.pk
            else:
                root_pk = self.kwargs['pk']  # in list and create
            kwargs.setdefault('root_pk', root_pk)
            context = super(CrudBaseMixin, self).get_context_data(**kwargs)

            if parent_object:
                context['title'] = '%s <small>(%s)</small>' % (
                    self.object, parent_object)

            return context

    class ListView(Crud.ListView):
        permission_required = RP_LIST,

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)/%s$' % cls.model._meta.model_name

        def get_context_data(self, **kwargs):
            obj = self.crud if hasattr(self, 'crud') else self
            context = CrudListView.get_context_data(self, **kwargs)

            parent_model = None
            if '__' in obj.parent_field:
                fields = obj.parent_field.split('__')
                parent_model = self.model
                for field in fields:
                    parent_model = getattr(
                        parent_model, field).field.related_model
            else:
                parent_model = getattr(
                    self.model, obj.parent_field).field.related_model

            params = {'pk': kwargs['root_pk']}

            if self.container_field:
                container = self.container_field.split('__')
                if len(container) > 1:
                    params['__'.join(container[1:])] = self.request.user.pk

            try:
                parent_object = parent_model.objects.get(**params)
            except:
                raise Http404()

            context[
                'title'] = '%s <small>(%s)</small>' % (
                context['title'], parent_object)
            return context

        def get_queryset(self):
            obj = self.crud if hasattr(self, 'crud') else self
            qs = super().get_queryset()

            kwargs = {obj.parent_field: self.kwargs['pk']}

            """if self.container_field:
                kwargs[self.container_field] = self.request.user.pk"""

            return qs.filter(**kwargs)

    class CreateView(Crud.CreateView):
        permission_required = RP_ADD,

        def dispatch(self, request, *args, **kwargs):
            return PermissionRequiredMixin.dispatch(
                self, request, *args, **kwargs)

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)/%s/create$' % cls.model._meta.model_name

        def get_form(self, form_class=None):
            obj = self.crud if hasattr(self, 'crud') else self
            form = super(MasterDetailCrud.CreateView, self).get_form(
                self.form_class)
            if not obj.is_m2m:
                parent_field = obj.parent_field.split('__')[0]
                field = self.model._meta.get_field(parent_field)
                parent = field.related_model.objects.get(pk=self.kwargs['pk'])
                setattr(form.instance, parent_field, parent)
            return form

        def get_context_data(self, **kwargs):
            obj = self.crud if hasattr(self, 'crud') else self
            context = Crud.CreateView.get_context_data(
                self, **kwargs)

            params = {'pk': self.kwargs['pk']}
            if self.container_field:
                parent_model = getattr(
                    self.model, obj.parent_field).field.related_model

                container = self.container_field.split('__')
                if len(container) > 1:
                    params['__'.join(container[1:])] = self.request.user.pk

                try:
                    parent = parent_model.objects.get(**params)
                except:
                    raise Http404()
            else:
                parent_field = obj.parent_field.split('__')[0]

                field = self.model._meta.get_field(parent_field)
                parent = field.related_model.objects.get(**params)
            if parent:
                context['title'] = '%s <small>(%s)</small>' % (
                    context['title'], parent)

            return context

    class UpdateView(Crud.UpdateView):
        permission_required = RP_CHANGE,

        @classmethod
        def get_url_regex(cls):
            return r'^%s/(?P<pk>\d+)/edit$' % cls.model._meta.model_name

    class DeleteView(Crud.DeleteView):
        permission_required = RP_DELETE,

        @classmethod
        def get_url_regex(cls):
            return r'^%s/(?P<pk>\d+)/delete$' % cls.model._meta.model_name

        def get_success_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            parent_object = getattr(
                self.get_object(), obj.parent_field)
            if not isinstance(parent_object, models.Model):
                if parent_object.count() > 1:
                    if 'pkk' not in self.request.GET:
                        raise Http404
                    root_pk = self.request.GET['pkk']
                    parent_object = parent_object.filter(id=root_pk)

                parent_object = parent_object.first()

                if not parent_object:
                    raise Http404
            root_pk = parent_object.pk

            pk = root_pk
            return self.resolve_url(ACTION_LIST, args=(pk,))

    class DetailView(Crud.DetailView):
        permission_required = RP_DETAIL,
        template_name = 'crud/detail_detail.html'

        @classmethod
        def get_url_regex(cls):
            return r'^%s/(?P<pk>\d+)$' % cls.model._meta.model_name

        @property
        def detail_list_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.ListView.permission_required or\
                    self.request.user.has_perm(self.permission(RP_LIST)):
                if '__' in obj.parent_field:
                    fields = obj.parent_field.split('__')
                    parent_object = self.object
                    for field in fields:
                        parent_object = getattr(parent_object, field)
                else:
                    parent_object = getattr(self.object, obj.parent_field)

                if not isinstance(parent_object, models.Model):
                    if parent_object.count() > 1:
                        if 'pkk' not in self.request.GET:
                            raise Http404
                        root_pk = self.request.GET['pkk']
                        parent_object = parent_object.filter(id=root_pk)

                    parent_object = parent_object.first()

                    if not parent_object:
                        raise Http404
                root_pk = parent_object.pk

                pk = root_pk
                return self.resolve_url(ACTION_LIST, args=(pk,))
            else:
                return ''

        @property
        def detail_create_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.CreateView:
                return ''

            if self.request.user.has_perm(self.permission(RP_ADD)):
                parent_field = obj.parent_field.split('__')[0]
                parent_object = getattr(self.object, parent_field)

                if not isinstance(parent_object, models.Model):
                    if parent_object.count() > 1:
                        if 'pkk' not in self.request.GET:
                            raise Http404
                        root_pk = self.request.GET['pkk']
                        parent_object = parent_object.filter(id=root_pk)

                    parent_object = parent_object.first()

                    if not parent_object:
                        raise Http404
                root_pk = parent_object.pk
                pk = root_pk
                return self.resolve_url(ACTION_CREATE, args=(pk,))
            else:
                return ''

        @property
        def detail_set_create_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if hasattr(obj, 'model_set') and obj.model_set\
                    and self.request.user.has_perm(
                        self.permission_set(RP_ADD)):
                root_pk = self.object .pk
                pk = root_pk
                return self.resolve_url_set(ACTION_CREATE, args=(pk,))
            else:
                return ''

        @property
        def detail_root_detail_url(self):
            """
            Implementar retorno para o parent_field imediato no caso de
            edição em cascata de MasterDetailDetail...
            """
            return ''

            obj = self.crud if hasattr(self, 'crud') else self
            if hasattr(obj, 'parent_field'):
                # parent_field = obj.parent_field.split('__')[0]

                root_pk = self.object .pk
                pk = root_pk
                return self.resolve_url(ACTION_DELETE, args=(pk,))
            else:
                return ''

    @classonlymethod
    def build(cls, model, parent_field, help_path,
              _model_set=None, list_field_names=[]):
        crud = super(MasterDetailCrud, cls).build(
            model, help_path, _model_set=_model_set,
            list_field_names=list_field_names)
        crud.parent_field = parent_field
        return crud


class CrudBaseForListAndDetailExternalAppView(MasterDetailCrud):
    CreateView, UpdateView, DeleteView = None, None, None

    class BaseMixin(Crud.PublicMixin, MasterDetailCrud.BaseMixin):

        @classmethod
        def url_name(cls, suffix):
            return '%s_parlamentar_%s' % (cls.model._meta.model_name, suffix)

        def resolve_url(self, suffix, args=None):
            obj = self.crud if hasattr(self, 'crud') else self

            """ namespace deve ser redirecionado para app local pois
            o models colocados nos cruds que herdam este Crud são de outras app
            """
            return reverse('%s:%s' % (obj.namespace, self.url_name(suffix)),
                           args=args)
