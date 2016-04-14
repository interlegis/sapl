from django.utils.decorators import classonlymethod

from .base import (CREATE, LIST, Crud, CrudBaseMixin, CrudCreateView,
                   CrudDeleteView, CrudDetailView, CrudListView,
                   CrudUpdateView)


class MasterDetailCrud(Crud):

    class BaseMixin(CrudBaseMixin):

        @property
        def list_url(self):
            return self.resolve_url(LIST, args=(self.kwargs['pk'],))

        @property
        def create_url(self):
            return self.resolve_url(CREATE, args=(self.kwargs['pk'],))

    class ListView(CrudListView):

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)/%s$' % cls.model._meta.model_name

        def get_queryset(self):
            qs = super(MasterDetailCrud.ListView, self).get_queryset()
            kwargs = {self.crud.parent_field: self.kwargs['pk']}
            return qs.filter(**kwargs)

    class CreateView(CrudCreateView):

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)/%s/create$' % cls.model._meta.model_name

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

    @classonlymethod
    def build(cls, model, parent_field, help_path):
        crud = super(MasterDetailCrud, cls).build(model, help_path)
        crud.parent_field = parent_field
        return crud
