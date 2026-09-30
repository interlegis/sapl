from collections import OrderedDict
from functools import cached_property
import django_filters
import importlib
import inspect
import logging
import re

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields.jsonb import JSONField
from django.contrib.auth import get_user_model
from django.db.models.base import ModelBase
from django.db.models.fields import TextField, CharField
from django.db.models.fields.files import FileField
from django.db.models.fields.related import ManyToManyField
from django.template.defaultfilters import capfirst
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django_filters.constants import ALL_FIELDS, EMPTY_VALUES
from django_filters.fields import ModelMultipleChoiceField
from django_filters.filters import CharFilter
from django_filters.filterset import FilterSet
from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.utils import resolve_field, get_all_model_fields
from rest_framework import serializers as rest_serializers
from rest_framework.relations import ManyRelatedField
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ModelViewSet
from rest_framework.urlpatterns import format_suffix_patterns


logger = logging.getLogger(__name__)


class SplitStringCharFilter(django_filters.CharFilter):
    _re = re.compile(r'("[^"]+"| +|[^"]+)')

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        lookup = '%s__%s' % (self.field_name, self.lookup_expr)

        values = [value]
        if self.lookup_expr == 'icontains':
            if not '"' in value:
                values = value.split(' ')
            else:
                values = list(
                    filter(
                        lambda x: x and x != ' ' and x[0] != '"',
                        self._re.findall(value)
                    )
                ) + list(
                    map(
                        lambda x: x[1:-1],
                        filter(
                            lambda x: x and x[0] == '"',
                            self._re.findall(value)
                        )
                    )
                )

        if not isinstance(values, list):
            values = [values]
        for v in values:
            qs = self.get_method(qs)(**{lookup: v})
        return qs


class M2MFilter(django_filters.ModelMultipleChoiceFilter):

    class M2MFieldFormField(ModelMultipleChoiceField):
        def clean(self, value):
            if value in EMPTY_VALUES:
                return super().clean(value)
            values = list(map(lambda x: x.replace(' ', '').split(','), value))
            values = [v for subvalues in values for v in subvalues]
            cleaned_values = tuple(super().clean(values))
            return (cleaned_values,) if cleaned_values else cleaned_values

    field_class = M2MFieldFormField
    distinct = True


class ApiFilterSetMixin(FilterSet):

    o = CharFilter(method='filter_o')
    id__in = CharFilter(method='filter_id__in')

    class Meta:
        fields = '__all__'
        filter_overrides = {
            FileField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
            CharField: {
                'filter_class': SplitStringCharFilter,
            },
            TextField: {
                'filter_class': SplitStringCharFilter,
            },
            JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'exact',
                },
            },
        }

    def filter_id__in(self, queryset, name, value):
        try:
            ids = [int(v.strip()) for v in value.split(',')]
            return queryset.filter(id__in=ids)
        except:
            return queryset

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
                    fields[f_str] = ['exact', 'in', ]
                    continue

                fields[f_str] = ['exact']

                def get_keys_lookups(cl, sub_f):
                    r = []
                    for lk, lv in cl.items():

                        if lk in ('contained_by', 'trigram_similar', 'unaccent', 'search'):
                            continue

                        sflk = f'{sub_f}{"__" if sub_f else ""}{lk}'
                        r.append(sflk)

                        if hasattr(lv, 'get_lookups'):
                            r += get_keys_lookups(lv.get_lookups(), sflk)

                        if hasattr(lv, 'output_field') and hasattr(lv, 'output_field.get_lookups'):
                            r.append(f'{sflk}{"__" if sflk else ""}range')

                            r += get_keys_lookups(lv.output_field.class_lookups, sflk)

                    return r

                fields[f_str] = list(
                    set(fields[f_str] + get_keys_lookups(f.get_lookups(), '')))

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

    @classmethod
    def filter_for_lookup(cls, field, lookup_type):
        f, p = super().filter_for_lookup(field, lookup_type)

        if lookup_type == 'in' and isinstance(field, ManyToManyField):
            return M2MFilter, p
        return f, p


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

    class LastModifiedDecorator(object):
        def __init__(self):
            pass
        def __call__(self, cls):
            return cls

    @classmethod
    def last_modified_class(cls, klass):
        cls.LastModifiedDecorator = klass
        return cls

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
    def router(cls, router_class = DefaultRouter):
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

                @cls.LastModifiedDecorator()
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


class DrfAutoApiSerializerMixin(rest_serializers.ModelSerializer):
    """
        Mixin de Serializer que implementa expansão dinâmica de campos
        via parâmetros de query string:
        - `expand`: expande os campos informados
        - `include`: inclui apenas os campos informados
        - `exclude`: exclui os campos informados

        Exemplo:
        - ?expand=campo1;campo2.sub_campo1,sub_campo2;campo3.sub_campo1.sub_sub_campo1,sub_sub_campo2
        - ?include=campo1;campo2.sub_campo1,sub_campo2;campo3.sub_campo1.sub_sub_campo1,sub_sub_campo2
        - ?exclude=campo1;campo2.sub_campo1,sub_campo2;campo3.sub_campo1.sub_sub_campo1,sub_sub_campo2
        - ?expand=campo1&include=campo1.id,name&exclude=campo1.secret_field

        Onde:
        - campo1, campo2, campo3 são campos do model raiz
        - sub_campo1, sub_campo2 são campos relacionados do campo2
        - sub_sub_campo1, sub_sub_campo2 são campos relacionados do sub_campo1

        Ou seja:
        ";" separa campos independentes do nível atual
        "," separa campos relacionados do mesmo campo pai
        "." indica o nível de profundidade dos campos relacionados

        e ainda:
        - `expand` pode ser usado para expansão direta, ou seja, campo1.sub_campo1 já expande campo1
        - `expand`, `include` e `exclude` podem ser usados juntos na mesma requisição
        - `include` e `exclude` só funcionam em subniveis se o campo pai estiver expandido
        - `include` tem precedência sobre `exclude` e já remove todo o resto
        - `exclude` remove o campo do resultado final, mesmo que esteja em `include`
        - Se nenhum dos parâmetros for informado, nenhum campo será expandido
        - Filtros da API, paginação (`page` e `page_size`) e ordenação (`o`)
            podem ser usados normalmente para filtrar os resultados

        Atenção:
        - A expansão não é aplicada para o model User do Django
        - A expansão não é aplicada para campos customizados que utilizam SerializerMethodField
        - Uma exceção é lançada e registrada no log caso ocorra algum erro na expansão de algum campo,
            inclusive devido a recursão infinita
        - A expansão automática de todos os campos relacionados (expand=all) está desabilitada
            por necessidade de controle mais refinado.
        - A expansão de campos relacionados ForeignKey e OneToOne é suportada.
        - A expansão de campos relacionados ManyToMany é suportada.
        - A expansão de campos relacionados reversos (related_name) não é suportada, mas pode ser implementada manualmente no serializer customizado, ou vir a ser implementada no futuro.
    """

    __str__ = rest_serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'

    def get___str__(self, obj) -> str:
        return str(obj)

    @cached_property
    def user_model(self):
        return get_user_model()

    def get_control_fields(self, control_field='expand'):
        request = self.context.get('request', None)
        if request:
            param = request.query_params.get(control_field, '')
            param = [e.strip() for e in param.split(';') if e.strip()]
            param = [e.split('.') for e in param]
            return param
        return []

    def get_fields(self):
        fields = super().get_fields()

        if not hasattr(self.root, 'drf_expand_fields'):
            self.root.drf_expand_fields = self.get_control_fields('expand')
            self.root.drf_include_fields = self.get_control_fields('include')
            self.root.drf_exclude_fields = self.get_control_fields('exclude')
            if not (self.root.drf_expand_fields or self.root.drf_include_fields or self.root.drf_exclude_fields):
                return fields

        model = self.Meta.model
        expand_fields = self.root.drf_expand_fields
        include_fields = self.root.drf_include_fields
        exclude_fields = self.root.drf_exclude_fields

        expand_all = False #['all'] in expand_fields

        #if expand_all:
        #    request = self.context.get('request', None)
        #    user = getattr(request, 'user', None)
        #    expand_all = user and user.is_superuser

        def parents(nd):
            if not nd:
                return []
            return parents(nd.parent) + [nd.field_name]

        sources = parents(self)
        sources = list(filter(lambda x: x, sources))

        if expand_fields:
            exps = []
            for exp in expand_fields:
                if len(exp) > len(sources) and exp[0:len(sources)] == sources:
                    exps.extend(exp[len(sources)].split(','))
            expand_fields = exps

        if include_fields:
            incls = []
            for inf in include_fields:
                if len(inf) - 1 == len(sources) and inf[:-1] == sources:
                    incls.extend(inf[-1].split(','))
            if incls:
                fields = OrderedDict(
                    [(k, v) for k, v in fields.items() if k in incls]
                )

        if exclude_fields:
            excls = []
            for inf in exclude_fields:
                if len(inf) - 1 == len(sources) and inf[:-1] == sources:
                    excls.extend(inf[-1].split(','))
            if excls:
                fields = OrderedDict(
                    [(k, v) for k, v in fields.items() if k not in excls]
                )

        fields_with_relations_map_model = {f.name: f.related_model for f in model._meta.get_fields()
                                  if f.is_relation and f.name in fields}

        set_fields_with_relations = set(fields_with_relations_map_model.keys())
        set_expand_fields = set(expand_fields)
        set_fields_serialized = set(
            map(
                lambda kv: kv[0],
                filter(
                    lambda kv: not isinstance(kv[1], rest_serializers.SerializerMethodField),
                    fields.items()
                )
            )
        )

        expand_fields = set_fields_with_relations.intersection(set_fields_serialized)

        if not expand_all:
            expand_fields = expand_fields.intersection(set_expand_fields)

        # remove o User model da expansão
        if self.user_model in fields_with_relations_map_model.values():
            expand_fields = [f for f in expand_fields
                             if fields_with_relations_map_model[f] != self.user_model]

        if not expand_fields:
            return fields

        for field_name in expand_fields:
            field = fields[field_name]

            model = fields_with_relations_map_model[field_name]

            if model:
                try:
                    serializer_class = ApiViewSetConstrutor.get_viewset_for_model(model).serializer_class
                    if hasattr(field, 'many') and field.many or isinstance(field, ManyRelatedField):
                        serializer_class = serializer_class(
                            many=True,
                            read_only=True,
                            context=self.context
                        )
                    else:
                        serializer_class = serializer_class(
                            read_only=True,
                            context=self.context
                        )

                    fields[field_name] = serializer_class

                except Exception as e:
                    logger.error(f'Erro ao expandir campo {field_name} do model {model}: {e}')

        return fields
