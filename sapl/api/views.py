from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from rest_framework.filters import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.viewsets import GenericViewSet
from sapl.api.forms import (AutorChoiceFilterSet, AutoresPossiveisFilterSet,
                            AutorSearchForFieldFilterSet)
from sapl.api.serializers import (AutorChoiceSerializer, AutorSerializer,
                                  ChoiceSerializer,
                                  MateriaLegislativaSerializer,
                                  ModelChoiceSerializer,
                                  SessaoPlenariaSerializer)
from sapl.base.models import Autor, TipoAutor
from sapl.materia.models import MateriaLegislativa
from sapl.sessao.models import SessaoPlenaria
from sapl.utils import SaplGenericRelation, sapl_logger


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
        try:
            tr = int(self.request.GET.get
                     ('tr', AutorListView.TR_AUTOR_CHOICE_SERIALIZER))

            assert tr in (
                AutorListView.TR_AUTOR_CHOICE_SERIALIZER,
                AutorListView.TR_AUTOR_SERIALIZER), sapl_logger.info(
                _("Tipo do Resultado a ser fornecido não existe!"))
        except:
            return AutorListView.TR_AUTOR_CHOICE_SERIALIZER
        else:
            return tr

    def get(self, request, *args, **kwargs):

        if self.tr == AutorListView.TR_AUTOR_SERIALIZER:
            self.serializer_class = AutorSerializer
            self.permission_classes = (IsAuthenticated,)

        if self.filter_class and 'q_0' in request.GET:
            self.filter_class = AutorSearchForFieldFilterSet

        return ListAPIView.get(self, request, *args, **kwargs)


class AutoresProvaveisListView(ListAPIView):

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Autor.objects.all()
    model = Autor

    filter_class = None
    filter_backends = []
    serializer_class = ChoiceSerializer

    def get_queryset(self):
        params = {'content_type__isnull': False}

        tipo = ''
        try:
            tipo = int(self.request.GET.get('tipo', ''))
            if tipo:
                params['id'] = tipo
        except:
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
    serializer_class = MateriaLegislativaSerializer
    queryset = MateriaLegislativa.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('numero', 'ano', 'tipo', )


class SessaoPlenariaViewSet(ListModelMixin,
                            RetrieveModelMixin,
                            GenericViewSet):

    permission_classes = (AllowAny,)
    serializer_class = SessaoPlenariaSerializer
    queryset = SessaoPlenaria.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('data_inicio', 'data_fim', 'interativa')
