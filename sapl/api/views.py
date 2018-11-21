
import logging

from django import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models import Q
from django.http import Http404
from django.utils.decorators import classonlymethod
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
from django_filters.utils import resolve_field
from rest_framework import serializers as rest_serializers
from rest_framework.decorators import list_route, detail_route
from rest_framework.filters import DjangoFilterBackend, FilterSet
from rest_framework.generics import ListAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly, AllowAny)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from sapl.api.forms import (AutorChoiceFilterSet, AutoresPossiveisFilterSet,
                            AutorSearchForFieldFilterSet)
from sapl.api.permissions import SaplModelPermissions
from sapl.api.serializers import (AutorChoiceSerializer, AutorSerializer,
                                  ChoiceSerializer,
                                  ModelChoiceSerializer,
                                  SessaoPlenariaOldSerializer,
                                  MateriaLegislativaOldSerializer)
from sapl.base.models import TipoAutor, Autor
from sapl.comissoes.models import Comissao
from sapl.materia.models import MateriaLegislativa, Proposicao
from sapl.parlamentares.models import Parlamentar
from sapl.rules.map_rules import __base__
from sapl.sessao.models import SessaoPlenaria
from sapl.utils import SaplGenericRelation


class ModelChoiceView(ListAPIView):

    # FIXME aplicar permissão correta de usuário
    permission_classes = (IsAuthenticated,)
    serializer_class = ModelChoiceSerializer

    def get(self, request, *args, **kwargs):
        self.model = ContentType.objects.get_for_id(
            self.kwargs['content_type']).model_class()

        pagination = request.GET.get('pagination', '')

        if pagination == 'False':
            self.pagination_class = None

        return ListAPIView.get(self, request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.all()


class AutorListView(ListAPIView):
    """
    Listagem de Autores com filtro para autores já cadastrados
    e/ou possíveis autores.

    - tr          - tipo do resultado
                    Prepera Lista de Autores para 3 cenários distintos

                    - default = 1

                  = 1 -> para (value, text) usados geralmente
                      em combobox, radiobox, checkbox, etc com pesquisa básica
                      de Autores feita pelo django-filter
                      -> processo usado nas pesquisas, o mais usado.


                  = 3 -> Devolve instancias da classe Autor filtradas pelo
                         django-filter

    - tipo      - chave primária do Tipo de Autor a ser filtrado

    - q         - busca textual no nome do Autor ou em  fields_search
                  declarados no field SaplGenericRelation das GenericFks
                      A busca textual acontece via django-filter com a
                      variável `tr` igual 1 ou 3. Em caso contrário,
                      o django-filter é desativado e a busca é feita
                      no model do ContentType associado ao tipo.

    - q_0 / q_1 - q_0 é opcional e quando usado, faz o código ignorar "q"...

                  q_0 -> campos lookup a serem filtrados em qualquer Model
                  que implemente SaplGenericRelation
                  q_1 -> o valor que será pesquisado no lookup de q_0

                  q_0 e q_1 podem ser separados por ","... isso dará a
                  possibilidade de filtrar mais de um campo.


                  http://localhost:8000
                      /api/autor?tr=1&q_0=parlamentar_set__ativo&q_1=False
                      /api/autor?tr=1&q_0=parlamentar_set__ativo&q_1=True
                      /api/autor?tr=3&q_0=parlamentar_set__ativo&q_1=False
                      /api/autor?tr=3&q_0=parlamentar_set__ativo&q_1=True

                  http://localhost:8000
                      /api/autor?tr=1
                          &q_0=parlamentar_set__nome_parlamentar__icontains,
                               parlamentar_set__ativo
                          &q_1=Carvalho,False
                      /api/autor?tr=1
                          &q_0=parlamentar_set__nome_parlamentar__icontains,
                               parlamentar_set__ativo
                          &q_1=Carvalho,True
                      /api/autor?tr=3
                          &q_0=parlamentar_set__nome_parlamentar__icontains,
                               parlamentar_set__ativo
                          &q_1=Carvalho,False
                      /api/autor?tr=3
                          &q_0=parlamentar_set__nome_parlamentar__icontains,
                               parlamentar_set__ativo
                          &q_1=Carvalho,True


                  não importa o campo que vc passe de qualquer dos Models
                  ligados... é possível ver que models são esses,
                      na ocasião do commit deste texto, executando:
                        In [6]: from sapl.utils import models_with_gr_for_model

                        In [7]: models_with_gr_for_model(Autor)
                        Out[7]:
                        [sapl.parlamentares.models.Parlamentar,
                         sapl.parlamentares.models.Frente,
                         sapl.comissoes.models.Comissao,
                         sapl.materia.models.Orgao,
                         sapl.sessao.models.Bancada,
                         sapl.sessao.models.Bloco]

                      qualquer atributo destes models podem ser passados
                      para busca
    """
    logger = logging.getLogger(__name__)

    TR_AUTOR_CHOICE_SERIALIZER = 1
    TR_AUTOR_SERIALIZER = 3

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Autor.objects.all()
    model = Autor

    filter_class = AutorChoiceFilterSet
    filter_backends = (DjangoFilterBackend, )
    serializer_class = AutorChoiceSerializer

    @property
    def tr(self):
        username = self.request.user.username
        try:
            tr = int(self.request.GET.get
                     ('tr', AutorListView.TR_AUTOR_CHOICE_SERIALIZER))

            if tr not in (AutorListView.TR_AUTOR_CHOICE_SERIALIZER,
                          AutorListView.TR_AUTOR_SERIALIZER):
                return AutorListView.TR_AUTOR_CHOICE_SERIALIZER
        except Exception as e:
            self.logger.error('user=' + username + '. ' + str(e))
            return AutorListView.TR_AUTOR_CHOICE_SERIALIZER
        return tr

    def get(self, request, *args, **kwargs):
        if self.tr == AutorListView.TR_AUTOR_SERIALIZER:
            self.serializer_class = AutorSerializer
            self.permission_classes = (IsAuthenticated,)

        if self.filter_class and 'q_0' in request.GET:
            self.filter_class = AutorSearchForFieldFilterSet

        return ListAPIView.get(self, request, *args, **kwargs)


class AutoresProvaveisListView(ListAPIView):
    logger = logging.getLogger(__name__)

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Autor.objects.all()
    model = Autor

    filter_class = None
    filter_backends = []
    serializer_class = ChoiceSerializer

    def get_queryset(self):

        params = {'content_type__isnull': False}
        username = self.request.user.username
        tipo = ''
        try:
            tipo = int(self.request.GET.get('tipo', ''))
            if tipo:
                params['id'] = tipo
        except Exception as e:
            self.logger.error('user= ' + username + '. ' + str(e))
            pass

        tipos = TipoAutor.objects.filter(**params)

        if not tipos.exists() and tipo:
            raise Http404()

        r = []
        for tipo in tipos:
            q = self.request.GET.get('q', '').strip()

            model_class = tipo.content_type.model_class()

            fields = list(filter(
                lambda field: isinstance(field, SaplGenericRelation) and
                field.related_model == Autor,
                model_class._meta.get_fields(include_hidden=True)))

            """
            fields - é um array de SaplGenericRelation que deve possuir o
                 atributo fields_search. Verifique na documentação da classe
                 a estrutura de fields_search.
            """

            assert len(fields) >= 1, (_(
                'Não foi encontrado em %(model)s um atributo do tipo '
                'SaplGenericRelation que use o model %(model_autor)s') % {
                'model': model_class._meta.verbose_name,
                'model_autor': Autor._meta.verbose_name})

            qs = model_class.objects.all()

            q_filter = Q()
            if q:
                for item in fields:
                    if item.related_model != Autor:
                        continue
                    q_fs = Q()
                    for field in item.fields_search:
                        q_fs = q_fs | Q(**{'%s%s' % (
                            field[0],
                            field[1]): q})
                    q_filter = q_filter & q_fs

                qs = qs.filter(q_filter).distinct(
                    fields[0].fields_search[0][0]).order_by(
                        fields[0].fields_search[0][0])
            else:
                qs = qs.order_by(fields[0].fields_search[0][0])

            qs = qs.values_list(
                'id', fields[0].fields_search[0][0])
            r += list(qs)

        if tipos.count() > 1:
            r.sort(key=lambda x: x[1].upper())
        return r


class AutoresPossiveisListView(ListAPIView):

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Autor.objects.all()
    model = Autor

    pagination_class = None

    filter_class = AutoresPossiveisFilterSet
    serializer_class = AutorChoiceSerializer


class MateriaLegislativaViewSet(ListModelMixin,
                                RetrieveModelMixin,
                                GenericViewSet):

    permission_classes = (IsAuthenticated,)
    serializer_class = MateriaLegislativaOldSerializer
    queryset = MateriaLegislativa.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('numero', 'ano', 'tipo', )


class SessaoPlenariaViewSet(ListModelMixin,
                            RetrieveModelMixin,
                            GenericViewSet):

    permission_classes = (AllowAny,)
    serializer_class = SessaoPlenariaOldSerializer
    queryset = SessaoPlenaria.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('data_inicio', 'data_fim', 'interativa')


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

                    @classmethod
                    def filter_for_field(cls, f, name, lookup_expr='exact'):
                        # Redefine método estático para ignorar filtro para
                        # fields que não possuam lookup_expr informado
                        f, lookup_type = resolve_field(f, lookup_expr)

                        default = {
                            'name': name,
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

    @list_route()
    def parlamentares(self, request, *args, **kwargs):
        # list /api/base/autor/parlamentares
        content_type = ContentType.objects.get_for_model(Parlamentar)
        return self.list_for_content_type(content_type)

    @list_route()
    def comissoes(self, request, *args, **kwargs):
        # list /api/base/autor/comissoes
        content_type = ContentType.objects.get_for_model(Comissao)
        return self.list_for_content_type(content_type)
    # Com isso redefinimos AutorViewSet com mais duas rotas
    # além das rotas padrão


class _ParlamentarViewSet(SaplSetViews['parlamentares']['parlamentar']):

    @detail_route()
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
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_anonymous():
            return qs.none()
        qs = qs.filter(autor__user=self.request.user)
        return qs


SaplSetViews['base']['autor'] = _AutorViewSet
SaplSetViews['materia']['proposicao'] = _ProposicaoViewSet
SaplSetViews['parlamentares']['parlamentar'] = _ParlamentarViewSet
