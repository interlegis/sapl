import logging

from django import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.fields.files import FileField
from django.utils.decorators import classonlymethod
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
import django_filters
from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from django_filters.utils import resolve_field
from rest_framework import serializers as rest_serializers
from rest_framework.decorators import list_route, detail_route, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from sapl.api.permissions import SaplModelPermissions
from sapl.comissoes.models import Comissao
from sapl.materia.models import Proposicao
from sapl.parlamentares.models import Parlamentar


class SaplApiViewSetConstrutor(ModelViewSet):

    filter_backends = (DjangoFilterBackend,)

    @classonlymethod
    def build_class(cls):
        import inspect
        from sapl.api import serializers

        # Carrega todas as classes de sapl.api.serializers que possuam
        # "Serializer" como Sufixo.
        serializers_classes = inspect.getmembers(serializers)
        serializers_classes = {i[0]: i[1] for i in filter(
            lambda x: x[0].endswith('Serializer'),
            serializers_classes
        )}

        # Carrega todas as classes de sapl.api.forms que possuam
        # "FilterSet" como Sufixo.
        from sapl.api import forms
        filters_classes = inspect.getmembers(forms)
        filters_classes = {i[0]: i[1] for i in filter(
            lambda x: x[0].endswith('FilterSet'),
            filters_classes
        )}

        built_sets = {}

        def build(_model):
            object_name = _model._meta.object_name

            # Caso Exista, pega a classe sapl.api.serializers.{model}Serializer
            serializer_name = '{model}Serializer'.format(model=object_name)
            _serializer_class = serializers_classes.get(serializer_name, None)

            # Caso Exista, pega a classe sapl.api.forms.{model}FilterSet
            filter_name = '{model}FilterSet'.format(model=object_name)
            _filter_class = filters_classes.get(filter_name, None)

            def create_class():
                # Define uma classe padrão para serializer caso não tenha sido
                # criada a classe sapl.api.serializers.{model}Serializer
                class SaplSerializer(rest_serializers.ModelSerializer):
                    class Meta:
                        model = _model
                        fields = '__all__'

                # Define uma classe padrão para filtro caso não tenha sido
                # criada a classe sapl.api.forms.{model}FilterSet
                class SaplFilterSet(FilterSet):
                    class Meta:
                        model = _model
                        fields = '__all__'
                        filter_overrides = {
                            FileField: {
                                'filter_class': django_filters.CharFilter,
                                'extra': lambda f: {
                                    'lookup_expr': 'exact',
                                },
                            },
                        }

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

                # Define uma classe padrão ModelViewSet de DRF
                class ModelSaplViewSet(cls):
                    queryset = _model.objects.all()

                    # Utiliza o filtro customizado pela classe
                    # sapl.api.forms.{model}FilterSet
                    # ou utiliza o trivial SaplFilterSet definido acima
                    filter_class = _filter_class \
                        if _filter_class else SaplFilterSet

                    # Utiliza o serializer customizado pela classe
                    # sapl.api.serializers.{model}Serializer
                    # ou utiliza o trivial SaplSerializer definido acima
                    serializer_class = _serializer_class \
                        if _serializer_class else SaplSerializer

                return ModelSaplViewSet

            viewset = create_class()
            viewset.__name__ = '%sModelSaplViewSet' % _model.__name__
            return viewset

        apps_sapl = [apps.apps.get_app_config(
            n[5:]) for n in settings.SAPL_APPS]
        for app in apps_sapl:
            built_sets[app.label] = {}
            for model in app.get_models():
                built_sets[app.label][model._meta.model_name] = build(model)

        return built_sets


"""
1. Constroi uma rest_framework.viewsets.ModelViewSet para 
   todos os models de todas as apps do sapl
2. Define DjangoFilterBackend como ferramenta de filtro dos campos
3. Define Serializer como a seguir:
    3.1 - Define um Serializer genérico para cada módel
    3.2 - Recupera Serializer customizado em sapl.api.serializers
    3.3 - Para todo model é opcional a existência de 
          sapl.api.serializers.{model}Serializer.
          Caso não seja definido um Serializer customizado, utiliza-se o trivial
4. Define um FilterSet como a seguir:
    4.1 - Define um FilterSet genérico para cada módel
    4.2 - Recupera FilterSet customizado em sapl.api.forms
    4.3 - Para todo model é opcional a existência de 
          sapl.api.forms.{model}FilterSet.
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

**SaplSetViews** é um dict de dicts de models conforme:
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

SaplSetViews = SaplApiViewSetConstrutor.build_class()

# Toda Classe construida acima, pode ser redefinida e aplicado quaisquer
# das possibilidades para uma classe normal criada a partir de
# rest_framework.viewsets.ModelViewSet conforme exemplo para a classe autor

# ALGUNS EXEMPLOS


class _AutorViewSet(SaplSetViews['base']['autor']):
    # OBS: esta classe é um exemplo e não contempla uma customização completa.
    """
    Neste exemplo de customização do que foi criado em 
    SaplApiViewSetConstrutor além do ofertado por 
    rest_framework.viewsets.ModelViewSet, dentre outras customizações
    possíveis, foi adicionado mais duas rotas, que neste exemplo seria:

    padrão de ModelViewSet
    http://localhost:9000/api/base/autor/       POST   - create
    http://localhost:9000/api/base/autor/       GET    - list     
    http://localhost:9000/api/base/autor/{pk}/  GET    - detail          
    http://localhost:9000/api/base/autor/{pk}/  PUT    - update
    http://localhost:9000/api/base/autor/{pk}/  DELETE - destroy

    rotas desta classe local:
    http://localhost:9000/api/base/autor/parlamentares
        devolve apenas autores que são parlamentares
    http://localhost:9000/api/base/autor/comissoes
        devolve apenas autores que são comissões

    estas mesmas listas oferecidas conforme acima, poderiam ser pesquisadas
    sabendo a informação que propicia seu filtro através, pois do django_filter

    no caso o ambiente de desenvolvimento no momento da escrita desse how-to:
    http://localhost:9000/api/base/autor/?content_type=26 para parlamentares
    http://localhost:9000/api/base/autor/?content_type=37 para comissoes

    diferenças como estas podem ser crusciais para uso da api
        neste caso em específico, content_types não são públicos e não possuem
        clareza
        isso:
        http://localhost:9000/api/base/autor/parlamentares
        faz o mesmo que isso:
        http://localhost:9000/api/base/autor/?content_type=26
        mas o primeiro é indiscutivelmente de melhor compreensão.

    """

    def list_for_content_type(self, content_type):
        qs = self.get_queryset()
        qs = qs.filter(content_type=content_type)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def parlamentares(self, request, *args, **kwargs):
        # list /api/base/autor/parlamentares
        content_type = ContentType.objects.get_for_model(Parlamentar)
        return self.list_for_content_type(content_type)

    @action(detail=False)
    def comissoes(self, request, *args, **kwargs):
        # list /api/base/autor/comissoes
        content_type = ContentType.objects.get_for_model(Comissao)
        return self.list_for_content_type(content_type)
    # Com isso redefinimos AutorViewSet com mais duas rotas
    # além das rotas padrão


class _ParlamentarViewSet(SaplSetViews['parlamentares']['parlamentar']):

    @action(detail=True)
    def proposicoes(self, request, *args, **kwargs):
        # /api/parlamentares/parlamentar/{pk}/proposicoes/
        # recupera proposições enviadas e incorporadas do parlamentar
        # deve coincidir com
        # /parlamentar/{pk}/proposicao
        content_type = ContentType.objects.get_for_model(Parlamentar)

        qs = Proposicao.objects.filter(
            data_envio__isnull=False,
            data_recebimento__isnull=False,
            cancelado=False,
            autor__object_id=kwargs['pk'],
            autor__content_type=content_type
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = SaplSetViews[
                'materia']['proposicao'].serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)


class _ProposicaoViewSet(SaplSetViews['materia']['proposicao']):
    """
    list:
        Retorna lista de Proposições

        * Permissões:

            * Usuário Dono:
                * Pode listar todas suas Proposições 

            * Usuário Conectado ou Anônimo:
                * Pode listar todas as Proposições incorporadas

    retrieve:
        Retorna uma proposição passada pelo 'id'

        * Permissões:

            * Usuário Dono:
                * Pode recuperar qualquer de suas Proposições 

            * Usuário Conectado ou Anônimo:
                * Pode recuperar qualquer das proposições incorporadas

    """
    class ProposicaoPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            if request.method == 'GET':
                return True
                # se a solicitação é list ou detail, libera o teste de permissão
                # e deixa o get_queryset filtrar de acordo com a regra de
                # visibilidade das proposições, ou seja:
                # 1. proposição incorporada é proposição pública
                # 2. não incorporada só o autor pode ver
            else:
                perm = super().has_permission(request, view)
                return perm
                # não é list ou detail, então passa pelas regras de permissão e,
                # depois disso ainda passa pelo filtro de get_queryset

    permission_classes = (ProposicaoPermission, )

    def get_queryset(self):
        qs = super().get_queryset()

        q = Q(data_recebimento__isnull=False, object_id__isnull=False)
        if not self.request.user.is_anonymous():
            q |= Q(autor__user=self.request.user)

        qs = qs.filter(q)
        return qs


SaplSetViews['base']['autor'] = _AutorViewSet
SaplSetViews['materia']['proposicao'] = _ProposicaoViewSet
SaplSetViews['parlamentares']['parlamentar'] = _ParlamentarViewSet
