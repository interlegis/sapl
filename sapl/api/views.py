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
from django_filters.filters import CharFilter
from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from django_filters.utils import resolve_field
from rest_framework import serializers as rest_serializers
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from sapl.api.forms import SaplFilterSetMixin
from sapl.api.permissions import SaplModelPermissions
from sapl.api.serializers import ChoiceSerializer
from sapl.base.models import Autor, AppConfig, DOC_ADM_OSTENSIVO
from sapl.materia.models import Proposicao, TipoMateriaLegislativa,\
    MateriaLegislativa, Tramitacao
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    DocumentoAcessorioAdministrativo, TramitacaoAdministrativo, Anexado
from sapl.sessao.models import SessaoPlenaria, ExpedienteSessao
from sapl.utils import models_with_gr_for_model, choice_anos_com_sessaoplenaria


class BusinessRulesNotImplementedMixin:
    def create(self, request, *args, **kwargs):
        raise Exception(_("POST Create não implementado"))

    def update(self, request, *args, **kwargs):
        raise Exception(_("PUT and PATCH não implementado"))

    def delete(self, request, *args, **kwargs):
        raise Exception(_("DELETE Delete não implementado"))


class SaplApiViewSet(ModelViewSet):
    filter_backends = (DjangoFilterBackend,)


class SaplApiViewSetConstrutor():

    _built_sets = {}

    @classonlymethod
    def get_class_for_model(cls, model):
        return cls._built_sets[model._meta.app_config][model]

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
                    __str__ = SerializerMethodField()

                    class Meta:
                        model = _model
                        fields = '__all__'

                    def get___str__(self, obj):
                        return str(obj)

                # Define uma classe padrão para filtro caso não tenha sido
                # criada a classe sapl.api.forms.{model}FilterSet
                class SaplFilterSet(SaplFilterSetMixin):
                    class Meta(SaplFilterSetMixin.Meta):
                        model = _model

                # Define uma classe padrão ModelViewSet de DRF
                class ModelSaplViewSet(SaplApiViewSet):
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
            cls._built_sets[app] = {}
            for model in app.get_models():
                cls._built_sets[app][model] = build(model)


SaplApiViewSetConstrutor.build_class()

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


# Customização para AutorViewSet com implementação de actions específicas


@customize(Autor)
class _AutorViewSet:
    """
    Neste exemplo de customização do que foi criado em 
    SaplApiViewSetConstrutor além do ofertado por 
    rest_framework.viewsets.ModelViewSet, dentre outras customizações
    possíveis, foi adicionado as rotas referentes aos relacionamentos genéricos

    * padrão de ModelViewSet
        /api/base/autor/       POST   - create
        /api/base/autor/       GET    - list     
        /api/base/autor/{pk}/  GET    - detail          
        /api/base/autor/{pk}/  PUT    - update      
        /api/base/autor/{pk}/  PATCH  - partial_update 
        /api/base/autor/{pk}/  DELETE - destroy

    * rotas desta classe local criadas pelo método build:
        /api/base/autor/parlamentar
            devolve apenas autores que são parlamentares
        /api/base/autor/comissao
            devolve apenas autores que são comissões
        /api/base/autor/bloco
            devolve apenas autores que são blocos parlamentares
        /api/base/autor/bancada
            devolve apenas autores que são bancadas parlamentares        
        /api/base/autor/frente
            devolve apenas autores que são Frene parlamentares
        /api/base/autor/orgao
            devolve apenas autores que são Órgãos
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

    @classonlymethod
    def build(cls):

        models_with_gr_for_autor = models_with_gr_for_model(Autor)

        for _model in models_with_gr_for_autor:

            @action(detail=False, name=_model._meta.model_name)
            def actionclass(self, request, *args, **kwargs):
                model = getattr(self, self.action)._AutorViewSet__model

                content_type = ContentType.objects.get_for_model(model)
                return self.list_for_content_type(content_type)

            func = actionclass
            func.mapping['get'] = func.kwargs['name']
            func.url_name = func.kwargs['name']
            func.url_path = func.kwargs['name']
            func.__model = _model

            setattr(cls, _model._meta.model_name, func)
        return cls


@customize(Parlamentar)
class _ParlamentarViewSet:
    @action(detail=True)
    def proposicoes(self, request, *args, **kwargs):
        """
        Lista de proposições públicas de parlamentar específico

        :param int id: - Identificador do parlamentar que se quer recuperar as proposições
        :return: uma lista de proposições
        """
        # /api/parlamentares/parlamentar/{id}/proposicoes/
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
            serializer = SaplApiViewSetConstrutor.get_class_for_model(
                Proposicao).serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)


@customize(Proposicao)
class _ProposicaoViewSet():
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


@customize(MateriaLegislativa)
class _MateriaLegislativaViewSet:

    @action(detail=True, methods=['GET'])
    def ultima_tramitacao(self, request, *args, **kwargs):

        materia = self.get_object()
        if not materia.tramitacao_set.exists():
            return Response({})

        ultima_tramitacao = materia.tramitacao_set.last()

        serializer_class = SaplApiViewSetConstrutor.get_class_for_model(
            Tramitacao).serializer_class(ultima_tramitacao)

        return Response(serializer_class.data)

    @action(detail=True, methods=['GET'])
    def anexadas(self, request, *args, **kwargs):
        self.queryset = self.get_object().anexadas.all()
        return self.list(request, *args, **kwargs)


@customize(TipoMateriaLegislativa)
class _TipoMateriaLegislativaViewSet:

    @action(detail=True, methods=['POST'])
    def change_position(self, request, *args, **kwargs):
        result = {
            'status': 200,
            'message': 'OK'
        }
        d = request.data
        if 'pos_ini' in d and 'pos_fim' in d:
            if d['pos_ini'] != d['pos_fim']:
                pk = kwargs['pk']
                TipoMateriaLegislativa.objects.reposicione(pk, d['pos_fim'])

        return Response(result)


@customize(DocumentoAdministrativo)
class _DocumentoAdministrativoViewSet:

    class DocumentoAdministrativoPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            if request.method == 'GET':
                comportamento = AppConfig.attr('documentos_administrativos')
                if comportamento == DOC_ADM_OSTENSIVO:
                    return True
                    """
                    Diante da lógica implementada na manutenção de documentos
                    administrativos:
                    - Se o comportamento é doc adm ostensivo, deve passar pelo 
                      teste de permissões sem avaliá-las
                    - se o comportamento é doc adm restritivo, deve passar pelo
                      teste de permissões avaliando-as
                    """
            return super().has_permission(request, view)

    permission_classes = (DocumentoAdministrativoPermission, )

    def get_queryset(self):
        """
        mesmo tendo passado pelo teste de permissões, deve ser filtrado,
        pelo campo restrito. Sendo este igual a True, disponibilizar apenas
        a um usuário conectado. Apenas isso, sem critérios outros de permissão, 
        conforme implementado em DocumentoAdministrativoCrud
        """
        qs = super().get_queryset()

        if self.request.user.is_anonymous():
            qs = qs.exclude(restrito=True)
        return qs


@customize(DocumentoAcessorioAdministrativo)
class _DocumentoAcessorioAdministrativoViewSet:

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission, )

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous():
            qs = qs.exclude(documento__restrito=True)
        return qs


@customize(TramitacaoAdministrativo)
class _TramitacaoAdministrativoViewSet(BusinessRulesNotImplementedMixin):
    # TODO: Implementar regras de manutenção das tramitações de docs adms

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission, )

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous():
            qs = qs.exclude(documento__restrito=True)
        return qs


@customize(Anexado)
class _AnexadoViewSet(BusinessRulesNotImplementedMixin):

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission, )

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous():
            qs = qs.exclude(documento__restrito=True)
        return qs


@customize(SessaoPlenaria)
class _SessaoPlenariaViewSet:

    @action(detail=False)
    def years(self, request, *args, **kwargs):
        years = choice_anos_com_sessaoplenaria()

        serializer = ChoiceSerializer(years, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def expedientes(self, request, *args, **kwargs):

        sessao = self.get_object()

        page = self.paginate_queryset(sessao.expedientesessao_set.all())
        if page is not None:
            serializer = SaplApiViewSetConstrutor.get_class_for_model(
                ExpedienteSessao).serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return Response(serializer.data)


@customize(NormaJuridica)
class _NormaJuridicaViewset:

    @action(detail=False, methods=['GET'])
    def destaques(self, request, *args, **kwargs):
        self.queryset = self.get_queryset().filter(norma_de_destaque=True)
        return self.list(request, *args, **kwargs)
