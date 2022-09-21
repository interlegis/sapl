from collections import OrderedDict
import importlib
import inspect
import logging

from django.apps.config import AppConfig
from django.apps.registry import apps
from django.conf import settings
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models.base import ModelBase
from django.db.models.fields.files import FileField
from django.template.defaultfilters import capfirst
from django.utils.translation import ugettext_lazy as _
import django_filters
from django_filters.constants import ALL_FIELDS
from django_filters.filters import CharFilter
from django_filters.filterset import FilterSet
from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.utils import resolve_field, get_all_model_fields
from rest_framework import serializers as rest_serializers
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ModelViewSet


logger = logging.getLogger(__name__)


class ApiFilterSetMixin(FilterSet):

    o = CharFilter(method='filter_o')

    class Meta:
        fields = '__all__'
        filter_overrides = {
            FileField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
            JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
        }

    def filter_o(self, queryset, name, value):
        try:
            return queryset.order_by(
                *map(str.strip, value.split(',')))
        except:
            return queryset

    @classmethod
    def get_fields(cls):
        model = cls._meta.model
        fields_model = get_all_model_fields(model)
        fields_filter = cls._meta.fields
        exclude = cls._meta.exclude

        if exclude is not None and fields_filter is None:
            fields_filter = ALL_FIELDS

        fields = fields_filter if isinstance(fields_filter, dict) else {}

        for f_str in fields_model:
            if f_str not in fields:

                f = model._meta.get_field(f_str)

                if f.many_to_many:
                    fields[f_str] = ['exact']
                    continue

                fields[f_str] = ['exact']

                def get_keys_lookups(cl, sub_f):
                    r = []
                    for lk, lv in cl.items():

                        if lk == 'contained_by':
                            continue

                        sflk = f'{sub_f}{"__" if sub_f else ""}{lk}'
                        r.append(sflk)

                        if hasattr(lv, 'class_lookups'):
                            r += get_keys_lookups(lv.class_lookups, sflk)

                        if hasattr(lv, 'output_field') and hasattr(lv, 'output_field.class_lookups'):
                            r.append(f'{sflk}{"__" if sflk else ""}range')

                            r += get_keys_lookups(lv.output_field.class_lookups, sflk)

                    return r

                fields[f_str] = list(
                    set(fields[f_str] + get_keys_lookups(f.class_lookups, '')))

        # Remove excluded fields
        exclude = exclude or []

        fields = [(f, lookups)
                  for f, lookups in fields.items() if f not in exclude]

        return OrderedDict(fields)

    @classmethod
    def filter_for_field(cls, f, name, lookup_expr='exact'):
        # Redefine método estático para ignorar filtro para
        # fields que não possuam lookup_expr informado

        f, lookup_type = resolve_field(f, lookup_expr)

        default = {
            'field_name': name,
            'label': capfirst(f.verbose_name),
            'lookup_expr': lookup_expr
        }

        filter_class, params = cls.filter_for_lookup(
            f, lookup_type)
        default.update(params)
        if filter_class is not None:
            return filter_class(**default)
        return None


class BusinessRulesNotImplementedMixin:
    http_method_names = ['get', 'head', 'options', 'trace']

    def create(self, request, *args, **kwargs):
        raise Exception(_("POST Create não implementado"))

    def update(self, request, *args, **kwargs):
        raise Exception(_("PUT and PATCH não implementado"))

    def delete(self, request, *args, **kwargs):
        raise Exception(_("DELETE Delete não implementado"))


class ApiViewSetConstrutor():

    _built_sets = {}

    class ApiViewSet(ModelViewSet):
        filter_backends = (DjangoFilterBackend,)

    @classmethod
    def get_viewset_for_model(cls, model):
        return cls._built_sets[model._meta.app_config][model]

    @classmethod
    def update(cls, other):
        cls._built_sets.update(other._built_sets)

    @classmethod
    def import_modules(cls, modules):
        for m in modules:
            importlib.import_module(m)

    @classmethod
    def router(cls, router_class=DefaultRouter):
        router = router_class()
        for app, built_sets in cls._built_sets.items():
            for model, viewset in built_sets.items():
                router.register(
                    f'{app.label}/{model._meta.model_name}', viewset)
        return router

    @classmethod
    def build_class(cls, apps_or_models):

        DRFAUTOAPI = settings.DRFAUTOAPI

        serializers_classes = {}
        filters_classes = {}

        global_serializer_mixin = rest_serializers.ModelSerializer
        global_filter_class = ApiFilterSetMixin

        try:
            if DRFAUTOAPI:
                if 'DEFAULT_SERIALIZER_MODULE' in DRFAUTOAPI:
                    serializers = importlib.import_module(
                        DRFAUTOAPI['DEFAULT_SERIALIZER_MODULE']
                    )
                    serializers_classes = inspect.getmembers(serializers)
                    serializers_classes = {i[0]: i[1] for i in filter(
                        lambda x: x[0].endswith('Serializer'),
                        serializers_classes
                    )}

                if 'DEFAULT_FILTER_MODULE' in DRFAUTOAPI:
                    filters = importlib.import_module(
                        DRFAUTOAPI['DEFAULT_FILTER_MODULE']
                    )
                    filters_classes = inspect.getmembers(filters)
                    filters_classes = {i[0]: i[1] for i in filter(
                        lambda x: x[0].endswith('FilterSet'),
                        filters_classes
                    )}

                if 'GLOBAL_SERIALIZER_MIXIN' in DRFAUTOAPI:
                    cs = DRFAUTOAPI['GLOBAL_SERIALIZER_MIXIN'].split('.')
                    module = importlib.import_module(
                        '.'.join(cs[0:-1]))
                    global_serializer_mixin = getattr(module, cs[-1])

                if 'GLOBAL_FILTERSET_MIXIN' in DRFAUTOAPI:
                    cs = DRFAUTOAPI['GLOBAL_FILTERSET_MIXIN'].split('.')
                    m = importlib.import_module('.'.join(cs[0:-1]))
                    global_filter_class = getattr(m, cs[-1])

        except Exception as e:
            logger.error(e)

        built_sets = {}

        def build(_model):
            object_name = _model._meta.object_name

            serializer_name = f'{object_name}Serializer'
            _serializer_class = serializers_classes.get(
                serializer_name, global_serializer_mixin)

            filter_name = f'{object_name}FilterSet'
            _filterset_class = filters_classes.get(
                filter_name, global_filter_class)

            def create_class():

                _meta_serializer = object if not hasattr(
                    _serializer_class, 'Meta') else _serializer_class.Meta

                class ApiSerializer(_serializer_class):

                    class Meta(_meta_serializer):
                        if not hasattr(_meta_serializer, 'ref_name'):
                            ref_name = f'{object_name}Serializer'

                        if not hasattr(_meta_serializer, 'model'):
                            model = _model

                        if hasattr(_meta_serializer, 'exclude'):
                            exclude = _meta_serializer.exclude
                        else:
                            if not hasattr(_meta_serializer, 'fields'):
                                fields = '__all__'
                            elif _meta_serializer.fields != '__all__':
                                fields = list(_meta_serializer.fields)
                            else:
                                fields = _meta_serializer.fields

                _meta_filterset = object if not hasattr(
                    _filterset_class, 'Meta') else _filterset_class.Meta

                class ApiFilterSet(_filterset_class):

                    class Meta(_meta_filterset, ):
                        if not hasattr(_meta_filterset, 'model'):
                            model = _model

                class ModelApiViewSet(ApiViewSetConstrutor.ApiViewSet):
                    queryset = _model.objects.all()
                    filterset_class = ApiFilterSet
                    serializer_class = ApiSerializer

                return ModelApiViewSet

            viewset = create_class()
            viewset.__name__ = '%sModelViewSet' % _model.__name__
            return viewset

        for am in apps_or_models:

            if isinstance(am, ModelBase):
                app = am._meta.app_config
            else:
                app = am

            if app not in cls._built_sets:
                cls._built_sets[app] = {}

            if am != app:
                cls._built_sets[app][am] = build(am)
                continue

            for model in app.get_models():
                cls._built_sets[app][model] = build(model)

        return cls


# Toda Classe construida acima, pode ser redefinida e aplicado quaisquer
# das possibilidades para uma classe normal criada a partir de
# rest_framework.viewsets.ModelViewSet conforme exemplo para a classe autor

# decorator que processa um endpoint detail trivial com base no model passado,
# Um endpoint detail geralmente é um conteúdo baseado numa FK com outros possíveis filtros
# e os passados pelo proprio cliente, além de o serializer e o filterset
# ser desse model passado


class wrapper_queryset_response_for_drf_action(object):

    def __init__(self, model):
        self.model = model

    def __call__(self, cls):

        def wrapper(instance_view, *args, **kwargs):
            # recupera a viewset do model anotado
            iv = instance_view
            viewset_from_model = ApiViewSetConstrutor._built_sets[
                self.model._meta.app_config][self.model]

            # apossa da instancia da viewset mae do action
            # em uma viewset que processa dados do model passado no decorator
            iv.queryset = viewset_from_model.queryset
            iv.serializer_class = viewset_from_model.serializer_class
            iv.filterset_class = viewset_from_model.filterset_class

            iv.queryset = instance_view.filter_queryset(
                iv.get_queryset())

            # chama efetivamente o metodo anotado que deve devolver um queryset
            # com os filtros específicos definido pelo programador customizador
            qs = cls(instance_view, *args, **kwargs)

            page = iv.paginate_queryset(qs)
            data = iv.get_serializer(
                page if page is not None else qs, many=True).data

            return iv.get_paginated_response(
                data) if page is not None else Response(data)

        return wrapper


# decorator para recuperar e transformar o default
class customize(object):

    def __init__(self, model):
        self.model = model

    def __call__(self, cls):

        class _ApiViewSet(
            cls,
                ApiViewSetConstrutor._built_sets[
                    self.model._meta.app_config][self.model]
        ):
            pass

        if hasattr(_ApiViewSet, 'build'):
            _ApiViewSet = _ApiViewSet.build()

        ApiViewSetConstrutor._built_sets[
            self.model._meta.app_config][self.model] = _ApiViewSet
        return _ApiViewSet
