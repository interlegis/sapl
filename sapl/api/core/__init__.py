import logging

from django import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import serializers as rest_serializers
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.fields import SerializerMethodField
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from sapl.api.core.filters import SaplFilterSetMixin
from sapl.api.permissions import SaplModelPermissions
from sapl.base.models import Metadata

# ATENÇÃO: MUDANÇAS NO CORE DEVEM SER REALIZADAS COM
#          EXTREMA CAUTELA


class BusinessRulesNotImplementedMixin:

    def create(self, request, *args, **kwargs):
        raise Exception(_("POST Create não implementado"))

    def update(self, request, *args, **kwargs):
        raise Exception(_("PUT and PATCH não implementado"))

    def delete(self, request, *args, **kwargs):
        raise Exception(_("DELETE Delete não implementado"))


class SaplApiViewSetConstrutor():

    class SaplApiViewSet(ModelViewSet):
        filter_backends = (DjangoFilterBackend,)

    _built_sets = {}

    @classonlymethod
    def get_class_for_model(cls, model):
        return cls._built_sets[model._meta.app_config][model]

    @classonlymethod
    def build_class(cls):
        import inspect
        from sapl.api.core import serializers

        # Carrega todas as classes de sapl.api.serializers que possuam
        # "Serializer" como Sufixo.
        serializers_classes = inspect.getmembers(serializers)

        serializers_classes = {i[0]: i[1] for i in filter(
            lambda x: x[0].endswith('Serializer'),
            serializers_classes
        )}

        # Carrega todas as classes de sapl.api.forms que possuam
        # "FilterSet" como Sufixo.
        from sapl.api.core import forms
        filters_classes = inspect.getmembers(forms)
        filters_classes = {i[0]: i[1] for i in filter(
            lambda x: x[0].endswith('FilterSet'),
            filters_classes
        )}

        built_sets = {}

        def build(_model):
            object_name = _model._meta.object_name

            # Caso Exista, pega a classe sapl.api.serializers.{model}Serializer
            # ou utiliza a base do drf para gerar uma automática para o model
            serializer_name = f'{object_name}Serializer'
            _serializer_class = serializers_classes.get(
                serializer_name, rest_serializers.ModelSerializer)

            # Caso Exista, pega a classe sapl.api.core.forms.{model}FilterSet
            # ou utiliza a base definida em
            # sapl.api.core.filters.SaplFilterSetMixin
            filter_name = f'{object_name}FilterSet'
            _filterset_class = filters_classes.get(
                filter_name, SaplFilterSetMixin)

            def create_class():

                _meta_serializer = object if not hasattr(
                    _serializer_class, 'Meta') else _serializer_class.Meta

                # Define uma classe padrão para serializer caso não tenha sido
                # criada a classe sapl.api.core.serializers.{model}Serializer
                class SaplSerializer(_serializer_class):
                    __str__ = SerializerMethodField()
                    metadata = SerializerMethodField()

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
                                fields = list(_meta_serializer.fields) + [
                                    '__str__', 'metadata']
                            else:
                                fields = _meta_serializer.fields

                    def get___str__(self, obj) -> str:
                        return str(obj)

                    def get_metadata(self, obj):
                        try:
                            metadata = Metadata.objects.get(
                                content_type=ContentType.objects.get_for_model(
                                    obj._meta.model),
                                object_id=obj.id
                            ).metadata
                        except:
                            metadata = {}
                        finally:
                            return metadata

                _meta_filterset = object if not hasattr(
                    _filterset_class, 'Meta') else _filterset_class.Meta

                # Define uma classe padrão para filtro caso não tenha sido
                # criada a classe sapl.api.forms.{model}FilterSet
                class SaplFilterSet(_filterset_class):

                    class Meta(_meta_filterset):
                        if not hasattr(_meta_filterset, 'model'):
                            model = _model

                # Define uma classe padrão ModelViewSet de DRF
                class ModelSaplViewSet(SaplApiViewSetConstrutor.SaplApiViewSet):
                    queryset = _model.objects.all()

                    # Utiliza o filtro customizado pela classe
                    # sapl.api.core.forms.{model}FilterSet
                    # ou utiliza o trivial SaplFilterSet definido acima
                    filterset_class = SaplFilterSet

                    # Utiliza o serializer customizado pela classe
                    # sapl.api.core.serializers.{model}Serializer
                    # ou utiliza o trivial SaplSerializer definido acima
                    serializer_class = SaplSerializer

                return ModelSaplViewSet

            viewset = create_class()
            viewset.__name__ = '%sModelSaplViewSet' % _model.__name__
            return viewset

        apps_sapl = [
            apps.apps.get_app_config('contenttypes')
        ] + [
            apps.apps.get_app_config(n[5:]) for n in settings.SAPL_APPS
        ]
        for app in apps_sapl:
            cls._built_sets[app] = {}
            for model in app.get_models():
                cls._built_sets[app][model] = build(model)

        return cls


"""
1. Constroi uma rest_framework.viewsets.ModelViewSet para
   todos os models de todas as apps do sapl
2. Define DjangoFilterBackend como ferramenta de filtro dos campos
3. Define Serializer como a seguir:
    3.1 - Define um Serializer genérico para cada módel
    3.2 - Recupera Serializer customizado em sapl.api.core.serializers
    3.3 - Para todo model é opcional a existência de
          sapl.api.core.serializers.{model}Serializer.
          Caso não seja definido um Serializer customizado, utiliza-se o trivial
4. Define um FilterSet como a seguir:
    4.1 - Define um FilterSet genérico para cada módel
    4.2 - Recupera FilterSet customizado em sapl.api.core.forms
    4.3 - Para todo model é opcional a existência de
          sapl.api.core.forms.{model}FilterSet.
          Caso não seja definido um FilterSet customizado, utiliza-se o trivial
    4.4 - todos os campos que aceitam lookup 'exact'
          podem ser filtrados por default

5. SaplApiViewSetConstrutor não cria padrões e/ou exige conhecimento alem dos
    exigidos pela DRF.

6. As rotas são criadas seguindo nome da app e nome do model
    http://localhost:9000/api/{applabel}/{model_name}/
    e seguem as variações definidas em:
    https://www.django-rest-framework.org/api-guide/routers/#defaultrouter

7. Todas as viewsets construídas por SaplApiViewSetConstrutor e suas rotas
    (paginate list, detail, edit, create, delete)
   bem como testes em ambiente de desenvolvimento podem ser conferidas em:
   http://localhost:9000/api/
   desde que settings.DEBUG=True

**SaplApiViewSetConstrutor._built_sets** é um dict de dicts de models conforme:
    {
        ...

        'audiencia': {
            'tipoaudienciapublica': TipoAudienciaPublicaViewSet,
            'audienciapublica': AudienciaPublicaViewSet,
            'anexoaudienciapublica': AnexoAudienciaPublicaViewSet

            ...

            },

        ...

        'base': {
            'casalegislativa': CasaLegislativaViewSet,
            'appconfig': AppConfigViewSet,

            ...

        }

        ...

    }
"""

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
            viewset_from_model = SaplApiViewSetConstrutor._built_sets[
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

        class _SaplApiViewSet(
            cls,
                SaplApiViewSetConstrutor._built_sets[
                    self.model._meta.app_config][self.model]
        ):
            pass

        if hasattr(_SaplApiViewSet, 'build'):
            _SaplApiViewSet = _SaplApiViewSet.build()

        SaplApiViewSetConstrutor._built_sets[
            self.model._meta.app_config][self.model] = _SaplApiViewSet
        return _SaplApiViewSet
