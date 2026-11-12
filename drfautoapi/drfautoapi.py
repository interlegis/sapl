from collections import OrderedDict
from functools import cached_property, partial
import django_filters
import importlib
import inspect
import logging
import re

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields.jsonb import JSONField
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Manager, Model, QuerySet
from django.db.models.base import ModelBase
from django.db.models.constants import LOOKUP_SEP
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
from rest_framework.relations import MANY_RELATION_KWARGS, \
    ManyRelatedField, PKOnlyObject
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ModelViewSet
from rest_framework.urlpatterns import format_suffix_patterns


logger = logging.getLogger(__name__)


def hidden_fields_for_model(model, request):
    """
    Campos de `model` ocultos para `request`, segundo o get_hidden_fields
    do serializer da viewset do model.
    """
    try:
        serializer_class = ApiViewSetConstrutor.get_viewset_for_model(
            model).serializer_class
    except KeyError:
        return set()

    hook = getattr(serializer_class, 'get_hidden_fields', None)
    return set(hook(request)) if hook else set()


def has_viewset(model):
    """Indica se a API tem uma viewset para `model`."""
    try:
        ApiViewSetConstrutor.get_viewset_for_model(model)
    except KeyError:
        return False
    return True


def visible_queryset(model, request):
    """
    Objetos de `model` que o usuário pode ver a partir de outro model nesta
    requisição: num campo expandido (?expand=) e, nos ManyToMany somente
    leitura, na lista de ids e no filtro pelo campo. Nenhum, se as
    permissões da viewset do model não permitirem listá-lo
    (has_expand_permission); senão, os do get_expand_queryset da viewset.
    Levanta KeyError se a API não tiver viewset para o model.
    """
    viewset = ApiViewSetConstrutor.get_viewset_for_model(model)
    if not viewset.has_expand_permission(request):
        return model._base_manager.none()
    return viewset.get_expand_queryset(request)


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # campos ocultos na resposta também não podem ser filtrados: o
        # filtro revelaria o valor por tentativa e erro
        hidden = self.get_hidden_fields()
        for name, f in list(self.filters.items()):
            if f.field_name in hidden:
                del self.filters[name]

        # num ManyToMany com model intermediário, somente leitura na API, a
        # resposta omite os objetos que o usuário não pode ver (ver
        # ApiManyRelatedField). No filtro pelo campo, eles são tratados como
        # inexistentes: senão, o filtro revelaria a relação por tentativa e
        # erro. Só os filtros usados na requisição são restringidos, para não
        # avaliar à toa as permissões do model relacionado
        for name, f in self.filters.items():
            if not isinstance(f, django_filters.ModelMultipleChoiceFilter):
                continue
            key = f'{self.form_prefix}-{name}' if self.form_prefix else name
            if key not in self.data:
                continue
            try:
                model_field = self._meta.model._meta.get_field(f.field_name)
            except FieldDoesNotExist:
                continue
            if model_field.many_to_many and \
                    not model_field.remote_field.through._meta.auto_created \
                    and has_viewset(model_field.related_model):
                f.queryset = partial(visible_queryset,
                                     model_field.related_model)

    def get_hidden_fields(self):
        return hidden_fields_for_model(self._meta.model, self.request)

    def filter_id__in(self, queryset, name, value):
        try:
            ids = [int(v.strip()) for v in value.split(',')]
            return queryset.filter(id__in=ids)
        except:
            return queryset

    def get_ordering_fields(self):
        """
        Campos aceitos em `o`: os campos concretos do próprio model (pelo
        nome ou pela coluna, como tipo_id), exceto os ocultos.
        """
        hidden = self.get_hidden_fields()
        fields = {'pk'}
        for f in self._meta.model._meta.concrete_fields:
            if f.name not in hidden:
                fields |= {f.name, f.attname}
        return fields

    def filter_o(self, queryset, name, value):
        """
        Ordena pelos campos informados, separados por vírgula, com "-" para
        ordem decrescente. O parâmetro é ignorado se algum campo não estiver
        em get_ordering_fields: caminhos para outros models (a__b) e campos
        ocultos permitiriam deduzir valores que não aparecem na resposta, e
        "?" ordena aleatoriamente, o que é caro.
        """
        fields = [f.strip() for f in value.split(',') if f.strip()]
        if not fields:
            return queryset

        allowed = self.get_ordering_fields()
        for f in fields:
            if (f[1:] if f.startswith('-') else f) not in allowed:
                return queryset

        return queryset.order_by(*fields)

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

        @classmethod
        def _expand_view(cls, request):
            """
            Instância da viewset como numa listagem pelo próprio endpoint,
            usada para decidir o que pode ser expandido a partir de outro
            model.
            """
            return cls(request=request, args=(), kwargs={},
                       format_kwarg=None, action='list')

        @classmethod
        def has_expand_permission(cls, request):
            """
            Indica se o model desta viewset pode ser expandido (?expand=) a
            partir de outro model nesta requisição. Por padrão, só quando as
            permissões da viewset permitiriam listar o model pelo próprio
            endpoint. Pode ser redefinido com @customize.
            """
            if request is None:
                return False

            view = cls._expand_view(request)
            return all(permission.has_permission(request, view)
                       for permission in view.get_permissions())

        @classmethod
        def get_expand_queryset(cls, request):
            """
            Objetos do model desta viewset que podem aparecer expandidos
            (?expand=) a partir de outro model nesta requisição. Os demais
            ficam só com o id, como sem o expand. Por padrão, são os do
            get_queryset da viewset, ou seja, os que o usuário veria pelo
            próprio endpoint, sem os filtros da query string, que se referem
            ao endpoint de origem. Pode ser redefinido com @customize.
            """
            return cls._expand_view(request).get_queryset()

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


def serializer_path(field):
    """
    Nomes dos campos desde o serializer raiz até `field`, como
    ('dispositivo', 'ta') em ?expand=dispositivo.ta. O filho de um
    ListSerializer não tem nome e não entra no caminho.
    """
    path = []
    while field is not None:
        if field.field_name:
            path.insert(0, field.field_name)
        field = field.parent
    return tuple(path)


class ExpandVisibility:
    """
    Quais objetos relacionados o usuário pode ver numa resposta: os dos
    campos expandidos (?expand=) e os dos ManyToMany somente leitura (ver
    ApiManyRelatedField).

    Um objeto só é serializado no campo expandido, ou listado no ManyToMany,
    se estiver em visible_queryset: as permissões da viewset do model dele
    precisam permitir listá-lo, e o objeto precisa estar no
    get_expand_queryset dela. Para não fazer uma query por objeto, cada
    caminho (como dispositivo.ta) é verificado de uma vez: a partir dos
    objetos do serializer raiz (a página da listagem ou o objeto do
    detalhe), uma única query busca, entre os objetos alcançados pelo
    caminho, os que o usuário pode ver.

    O estado fica no contexto do serializer raiz, compartilhado por todos os
    serializers da resposta.
    """

    context_key = '_drfautoapi_expand_visibility'

    def __init__(self, request):
        self.request = request
        self.querysets = {}
        self.unfiltered = {}
        self.visible_by_path = {}
        self.visible_by_object = {}

    @classmethod
    def for_field(cls, field):
        context = field.context
        if cls.context_key not in context:
            context[cls.context_key] = cls(context.get('request', None))
        return context[cls.context_key]

    def queryset(self, model):
        if model not in self.querysets:
            try:
                queryset = visible_queryset(model, self.request).order_by()
            except Exception as e:
                logger.error(f'Erro ao obter os objetos de {model} que '
                             f'podem ser expandidos: {e}')
                queryset = model._base_manager.none()
            self.querysets[model] = queryset
        return self.querysets[model]

    def all_visible(self, model):
        """
        Indica se o usuário pode ver todos os objetos de `model`, ou seja, se
        o queryset dos visíveis não tem nenhum filtro, como num model público
        ou para quem pode ver tudo. Nesse caso, a verificação dispensa
        queries.
        """
        if model not in self.unfiltered:
            query = self.queryset(model).query
            self.unfiltered[model] = not (
                query.where or query.combinator or query.distinct_fields or
                query.extra_tables or not query.can_filter())
        return self.unfiltered[model]

    def is_visible(self, field, model, pk):
        if self.all_visible(model):
            return True

        path = serializer_path(field)
        if path not in self.visible_by_path:
            self.visible_by_path[path] = self.visible_in_path(
                field.root, path, model)

        visible = self.visible_by_path[path]
        if visible is not None:
            return pk in visible

        # o caminho não pôde ser verificado de uma vez: verifica o objeto
        key = (model, pk)
        if key not in self.visible_by_object:
            try:
                self.visible_by_object[key] = self.queryset(
                    model).filter(pk=pk).exists()
            except Exception as e:
                logger.error(f'Erro ao verificar se o objeto {pk} de {model} '
                             f'pode ser expandido: {e}')
                self.visible_by_object[key] = False
        return self.visible_by_object[key]

    def visible_in_path(self, root, path, model):
        """
        pks visíveis de `model` entre os objetos alcançados por `path` a
        partir das instâncias do serializer raiz, ou None se não for possível
        consultá-los de uma vez, por exemplo, se o caminho passar por um
        campo que não é do model.
        """
        instances = root.instance
        if instances is None:
            return None
        if isinstance(root, rest_serializers.ListSerializer):
            if isinstance(instances, Manager):
                instances = instances.all()
            # um iterador seria consumido aqui, e a resposta sairia sem
            # esses objetos
            if not isinstance(instances, (list, tuple, QuerySet)):
                return None
            instances = list(instances)
        else:
            instances = [instances]

        if not instances:
            return set()

        root_model = type(instances[0])
        if not issubclass(root_model, Model) or any(
                type(i) is not root_model for i in instances):
            return None

        try:
            reached = root_model._base_manager.filter(
                pk__in=[i.pk for i in instances]
            ).values(LOOKUP_SEP.join(path))
            return set(self.queryset(model).filter(
                pk__in=reached).values_list('pk', flat=True))
        except Exception as e:
            logger.error(f'Erro ao verificar os objetos expandidos em '
                         f'{".".join(path)}: {e}')
            return None


class ExpandedSerializerMixin:
    """
    Serializer de um campo expandido (?expand=) que aponta para um único
    objeto, como uma ForeignKey. Se o usuário não puder ver o objeto (ver
    ExpandVisibility), o campo fica só com o id, como sem o expand, e o
    objeto nem é buscado.
    """

    def get_attribute(self, instance):
        visibility = ExpandVisibility.for_field(self)
        model = self.Meta.model

        attname = None
        if len(self.source_attrs) == 1:
            try:
                model_field = instance._meta.get_field(self.source_attrs[0])
            except (AttributeError, FieldDoesNotExist):
                model_field = None
            if model_field is not None and model_field.concrete and (
                    model_field.many_to_one or model_field.one_to_one) and \
                    model_field.target_field.primary_key:
                attname = model_field.attname

        if attname is not None:
            pk = getattr(instance, attname)
            if pk is None:
                return None
            if not visibility.is_visible(self, model, pk):
                return PKOnlyObject(pk=pk)
            return super().get_attribute(instance)

        related = super().get_attribute(instance)
        if related is not None and not visibility.is_visible(
                self, model, related.pk):
            return PKOnlyObject(pk=related.pk)
        return related

    def to_representation(self, instance):
        if isinstance(instance, PKOnlyObject):
            return instance.pk
        return super().to_representation(instance)


class ExpandedListSerializer(rest_serializers.ListSerializer):
    """
    Campo expandido (?expand=) com vários objetos, como um ManyToMany. Os
    objetos que o usuário não pode ver (ver ExpandVisibility) ficam como no
    campo sem o expand (ver ApiManyRelatedField): são omitidos se o campo
    original for somente leitura (omit_hidden) e ficam só com o id se ele
    for editável.
    """

    def __init__(self, *args, omit_hidden=False, **kwargs):
        self.omit_hidden = omit_hidden
        super().__init__(*args, **kwargs)

    def to_representation(self, data):
        visibility = ExpandVisibility.for_field(self)
        model = self.child.Meta.model
        iterable = data.all() if isinstance(data, Manager) else data
        representation = []
        for item in iterable:
            if visibility.is_visible(self, model, item.pk):
                representation.append(self.child.to_representation(item))
            elif not self.omit_hidden:
                representation.append(item.pk)
        return representation


class ApiManyRelatedField(ManyRelatedField):
    """
    ManyToMany sem expand. Se o campo for somente leitura, como os
    ManyToMany com model intermediário (through), os objetos que o usuário
    não pode ver (ver ExpandVisibility) são omitidos da lista. Num campo
    editável, todos os ids continuam na lista: o cliente a devolve no
    PUT/PATCH, e omitir um id apagaria a relação com o objeto oculto.

    Models sem viewset na API, como o User, não têm regra de visibilidade, e
    os ids deles continuam todos na lista.
    """

    def to_representation(self, iterable):
        model = getattr(iterable, 'model', None)
        if not self.read_only or model is None or not has_viewset(model) or \
                self.context.get('request', None) is None:
            return super().to_representation(iterable)

        visibility = ExpandVisibility.for_field(self)
        return [
            self.child_relation.to_representation(item)
            for item in iterable
            if visibility.is_visible(self, model, item.pk)
        ]


class ApiPrimaryKeyRelatedField(rest_serializers.PrimaryKeyRelatedField):
    """
    PrimaryKeyRelatedField que, com many=True, cria um ApiManyRelatedField.
    """

    @classmethod
    def many_init(cls, *args, **kwargs):
        # como RelatedField.many_init, trocando só a classe do campo
        list_kwargs = {'child_relation': cls(*args, **kwargs)}
        for key in kwargs:
            if key in MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]
        return ApiManyRelatedField(**list_kwargs)


_expanded_serializer_classes = {}


def expanded_serializer_class(serializer_class):
    """serializer_class com o comportamento de ExpandedSerializerMixin."""
    expanded = _expanded_serializer_classes.get(serializer_class)
    if expanded is None:
        expanded = type(serializer_class)(
            f'Expanded{serializer_class.__name__}',
            (ExpandedSerializerMixin, serializer_class), {})
        _expanded_serializer_classes[serializer_class] = expanded
    return expanded


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
        - A expansão só é aplicada a models que o usuário poderia listar pelo
            próprio endpoint (ver ApiViewSet.has_expand_permission)
        - Cada objeto expandido também precisa estar entre os que o usuário
            veria pelo endpoint do model dele (ver
            ApiViewSet.get_expand_queryset). Os demais ficam só com o id, como
            sem o expand. A verificação é feita de uma vez para cada campo
            expandido da resposta (ver ExpandVisibility)
        - Num ManyToMany somente leitura, como os que têm model intermediário,
            os objetos que o usuário não veria pelo endpoint do model deles
            são omitidos, com ou sem o expand (ver ApiManyRelatedField), e o
            filtro pelo campo os trata como inexistentes
        - Campos devolvidos por get_hidden_fields são removidos em qualquer
            nível, inclusive quando o model é expandido a partir de outro
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

    serializer_related_field = ApiPrimaryKeyRelatedField

    class Meta:
        fields = '__all__'

    def get___str__(self, obj) -> str:
        return str(obj)

    @classmethod
    def get_hidden_fields(cls, request):
        """
        Campos do model que não devem ser expostos nesta requisição. Eles
        saem da resposta, também quando o model é expandido a partir de
        outro, e não podem ser usados em filtros nem na ordenação (`o`).
        `request` pode ser None, quando o serializer é usado sem contexto.
        """
        return set()

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

        request = self.context.get('request', None)
        for field_name in self.get_hidden_fields(request):
            fields.pop(field_name, None)

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
                    viewset = ApiViewSetConstrutor.get_viewset_for_model(model)
                    if not viewset.has_expand_permission(request):
                        continue

                    serializer_class = viewset.serializer_class
                    kwargs = {'read_only': True, 'context': self.context}
                    if hasattr(field, 'many') and field.many or isinstance(field, ManyRelatedField):
                        fields[field_name] = ExpandedListSerializer(
                            child=serializer_class(**kwargs),
                            omit_hidden=field.read_only, **kwargs)
                    else:
                        fields[field_name] = expanded_serializer_class(
                            serializer_class)(**kwargs)

                except Exception as e:
                    logger.error(f'Erro ao expandir campo {field_name} do model {model}: {e}')

        return fields
