from django.db.models import Q
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from rest_framework.filters import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from sapl.api.forms import AutorChoiceFilterSet
from sapl.api.serializers import (AutorChoiceSerializer, AutorSerializer,
                                  ChoiceSerializer)
from sapl.base.models import Autor, TipoAutor
from sapl.utils import SaplGenericRelation, sapl_logger


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

                  = 2 -> para (value, text) usados geralmente
                      em combobox, radiobox, checkbox, etc com pesquisa básica
                      de Autores mas feito para Possíveis Autores armazenados
                      segundo o ContentType associado ao Tipo de Autor via
                      relacionamento genérico.
                      Busca feita sem django-filter processada no get_queryset
                      -> processo no cadastro de autores para seleção e busca
                          dos possíveis autores

                  = 3 -> Devolve instancias da classe Autor filtradas pelo
                         django-filter

    - tipo      - chave primária do Tipo de Autor a ser filtrado

    - q         - busca textual no nome do Autor ou em  fields_search
                  declarados no field SaplGenericRelation das GenericFks
                      A busca textual acontece via django-filter com a
                      variável `tr` igual 1 ou 3. Em caso contrário,
                      o django-filter é desativado e a busca é feita
                      no model do ContentType associado ao tipo.

    Outros campos
    """

    TR_AUTOR_CHOICE_SERIALIZER = 1
    TR_CHOICE_SERIALIZER = 2
    TR_AUTOR_SERIALIZER = 3

    # FIXME aplicar permissão correta de usuário
    permission_classes = (AllowAny,)
    serializer_class = AutorSerializer
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
                AutorListView.TR_CHOICE_SERIALIZER,
                AutorListView.TR_AUTOR_SERIALIZER), sapl_logger.info(
                _("Tipo do Resultado a ser fornecido não existe!"))
        except:
            return AutorListView.TR_AUTOR_CHOICE_SERIALIZER
        else:
            return tr

    def get(self, request, *args, **kwargs):
        """
            desativa o django-filter se a busca for por possiveis autores
            parametro tr = TR_CHOICE_SERIALIZER
        """

        if self.tr == AutorListView.TR_CHOICE_SERIALIZER:
            self.filter_class = None
            self.filter_backends = []
            self.serializer_class = ChoiceSerializer

        elif self.tr == AutorListView.TR_AUTOR_SERIALIZER:
            self.serializer_class = AutorSerializer
            self.permission_classes = (IsAuthenticated,)

        return ListAPIView.get(self, request, *args, **kwargs)

    def get_queryset(self):
        queryset = ListAPIView.get_queryset(self)

        if self.filter_backends:
            return queryset

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
                    fields[0].fields_search[0][0])

            qs = qs.order_by(fields[0].fields_search[0][0]).values_list(
                'id', fields[0].fields_search[0][0])
            r += list(qs)

        if tipos.count() > 1:
            r.sort(key=lambda x: x[1].upper())
        return r
