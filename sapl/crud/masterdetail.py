from django.utils.decorators import classonlymethod

from .base import (ACTION_CREATE, ACTION_LIST, Crud, CrudBaseMixin, CrudCreateView,
                   CrudDeleteView, CrudDetailView, CrudListView,
                   CrudUpdateView)


class MasterDetailCrud__OBSOLETO(Crud):

    class BaseMixin(CrudBaseMixin):

        @property
        def list_url(self):
            return self.resolve_url(ACTION_LIST, args=(self.kwargs['pk'],))

        @property
        def create_url(self):
            return self.resolve_url(ACTION_CREATE, args=(self.kwargs['pk'],))

        def get_context_data(self, **kwargs):
            obj = getattr(self, 'object', None)
            if obj:
                root_pk = getattr(obj, self.crud.parent_field).pk
            else:
                root_pk = self.kwargs['pk']  # in list and create
            kwargs.setdefault('root_pk', root_pk)
            return super(MasterDetailCrud__OBSOLETO.BaseMixin,
                         self).get_context_data(**kwargs)

    class ListView(CrudListView):

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)/%s$' % cls.model._meta.model_name

        def get_queryset(self):
            qs = super(
                MasterDetailCrud__OBSOLETO.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs)

    class CreateView(CrudCreateView):

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)/%s/create$' % cls.model._meta.model_name

        def get_form(self, form_class=None):
            form = super(MasterDetailCrud__OBSOLETO.CreateView,
                         self).get_form(self.form_class)
            field = self.model._meta.get_field(self.crud.parent_field)
            parent = field.related_model.objects.get(pk=self.kwargs['pk'])
            setattr(form.instance, self.crud.parent_field, parent)
            return form

    class DetailView(CrudDetailView):

        @classmethod
        def get_url_regex(cls):
            return r'^%s/(?P<pk>\d+)$' % cls.model._meta.model_name

    class UpdateView(CrudUpdateView):

        @classmethod
        def get_url_regex(cls):
            return r'^%s/(?P<pk>\d+)/edit$' % cls.model._meta.model_name

    class DeleteView(CrudDeleteView):

        @classmethod
        def get_url_regex(cls):
            return r'^%s/(?P<pk>\d+)/delete$' % cls.model._meta.model_name

        def get_success_url(self):
            pk = getattr(self.get_object(), self.crud.parent_field).pk
            return self.resolve_url(ACTION_LIST, args=(pk,))

    @classonlymethod
    def build(cls, model, parent_field, help_path):
        crud = super(MasterDetailCrud__OBSOLETO, cls).build(model, help_path)
        crud.parent_field = parent_field
        return crud
