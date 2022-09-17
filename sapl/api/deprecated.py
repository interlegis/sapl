import logging

from django.db.models import Q
from django.forms.fields import CharField, MultiValueField
from django.forms.widgets import MultiWidget, TextInput
from django.http import Http404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_filters.filters import CharFilter, ModelChoiceFilter, DateFilter
from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly, AllowAny)
from rest_framework.relations import StringRelatedField
from rest_framework.viewsets import GenericViewSet

from sapl.api.serializers import AutorSerializer, ModelChoiceSerializer,\
    ChoiceSerializer, SessaoPlenariaECidadaniaSerializer
from sapl.base.models import TipoAutor, Autor, CasaLegislativa
from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import Legislatura
from sapl.sessao.models import SessaoPlenaria, OrdemDia
from sapl.utils import SaplGenericRelation
from sapl.utils import generic_relations_for_model


class SaplGenericRelationSearchFilterSet(FilterSet):
    q = CharFilter(method='filter_q')

    def filter_q(self, queryset, name, value):

        query = value.split(' ')
        if query:
            q = Q()
            for qtext in query:
                if not qtext:
                    continue
                q_fs = Q(nome__icontains=qtext)

                order_by = []

                for gr in generic_relations_for_model(self._meta.model):
                    sgr = gr[1]
                    for item in sgr:
                        if item.related_model != self._meta.model:

                            continue
                        flag_order_by = True
                        for field in item.fields_search:
                            if flag_order_by:
                                flag_order_by = False
                                order_by.append('%s__%s' % (
                                    item.related_query_name(),
                                    field[0])
                                )
                            # if len(field) == 3 and field[2](qtext) is not
                            # None:
                            q_fs = q_fs | Q(**{'%s__%s%s' % (
                                item.related_query_name(),
                                field[0],
                                field[1]): qtext if len(field) == 2
                                else field[2](qtext)})

                q = q & q_fs

            if q:
                queryset = queryset.filter(q).order_by(*order_by)

        return queryset


class SearchForFieldWidget(MultiWidget):

    def decompress(self, value):
        if value is None:
            return [None, None]
        return value

    def __init__(self, attrs=None):
        widgets = (TextInput, TextInput)
        MultiWidget.__init__(self, widgets, attrs)


class SearchForFieldField(MultiValueField):
    widget = SearchForFieldWidget

    def __init__(self, *args, **kwargs):
        fields = (
            CharField(),
            CharField())
        super(SearchForFieldField, self).__init__(fields, *args, **kwargs)

    def compress(self, parameters):
        if parameters:
            return parameters
        return None


class SearchForFieldFilter(CharFilter):
    field_class = SearchForFieldField


class AutorChoiceFilterSet(SaplGenericRelationSearchFilterSet):
    q = CharFilter(method='filter_q')
    tipo = ModelChoiceFilter(queryset=TipoAutor.objects.all())

    class Meta:
        model = Autor
        fields = ['q',
                  'tipo',
                  'nome', ]

    def filter_q(self, queryset, name, value):
        return super().filter_q(
            queryset, name, value).distinct('nome').order_by('nome')


class AutorSearchForFieldFilterSet(AutorChoiceFilterSet):
    q = SearchForFieldFilter(method='filter_q')

    class Meta(AutorChoiceFilterSet.Meta):
        pass

    def filter_q(self, queryset, name, value):

        value[0] = value[0].split(',')
        value[1] = value[1].split(',')

        params = {}
        for key, v in list(zip(value[0], value[1])):
            if v in ['True', 'False']:
                v = '1' if v == 'True' else '0'
            params[key] = v
        return queryset.filter(**params).distinct('nome').order_by('nome')


class AutorChoiceSerializer(ModelChoiceSerializer):

    def get_text(self, obj):
        return obj.nome

    class Meta:
        model = Autor
        fields = ['id', 'nome']


class AutorListView(ListAPIView):
    """
    Deprecated

    TODO Migrar para customização na api automática

    Listagem de Autores com filtro para autores já cadastrados
    e/ou possíveis autores.

    - tr - tipo do resultado
      Prepera Lista de Autores para 2 cenários distintos

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
    filter_backends = (DjangoFilterBackend,)
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


class SessaoPlenariaViewSet(ListModelMixin,
                            RetrieveModelMixin,
                            GenericViewSet):
    """
    Deprecated

    TODO Migrar para customização na api automática
    """

    permission_classes = (AllowAny,)
    serializer_class = SessaoPlenariaECidadaniaSerializer
    queryset = SessaoPlenaria.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('data_inicio', 'data_fim', 'interativa')
