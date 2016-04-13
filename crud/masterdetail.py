from .base import (Crud, CrudCreateView, CrudDeleteView, CrudDetailView,
                   CrudListView, CrudUpdateView)


class MasterDetailCrud(Crud):

    class ListView(CrudListView):

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)/%s$' % cls.model._meta.model_name

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
