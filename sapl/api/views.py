
from django.db.models import Q
from django.http import Http404
from rest_framework.filters import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from sapl.api.forms import AutorChoiceFilterSet
from sapl.api.serializers import ChoiceSerializer, AutorSerializer,\
    AutorChoiceSerializer
from sapl.base.models import Autor, TipoAutor
from sapl.utils import SaplGenericRelation


class AutorListView(ListAPIView):
    """
    Listagem de Autores com filtro para autores já cadastrados
    e/ou possíveis autores.

    - tipo      - chave primária do Tipo de Autor a ser filtrado
    - provaveis - variável sem relevância de valor, porém, sua presença
                  faz com que a AutorListView
                  mostre a lista de provaveis Autores armazenados segundo o
                  ContentType associado ao Tipo de Autor via relacionamento
                  genérico.
    - q         - busca textual no nome do Autor ou em  fields_search
                  declarados no field SaplGenericRelation das GenericFks

                      A busca textual acontece via django-filter se não
                      estiver presente a variável `provaveis`. Em caso
                      contrário, o django-filter é desativado e a busca é feita
                      no model do ContentType associado ao tipo.
    """
    # FIXME aplicar permissão correta de usuário
    permission_classes = (IsAuthenticated,)
    serializer_class = AutorSerializer
    queryset = Autor.objects.all()
    model = Autor

    def get(self, request, *args, **kwargs):
        """
            desativa o django-filter se a busca for por provaveis autores
        """
        provaveis = 'provaveis' in request.GET
        self.filter_class = None if provaveis else AutorChoiceFilterSet
        self.filter_backends = [] if provaveis else [DjangoFilterBackend]
        self.serializer_class = ChoiceSerializer\
            if provaveis else AutorChoiceSerializer

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

            # retirar assert
            assert len(fields) == 1

            qs = model_class.objects.all().order_by(
                fields[0].fields_search[0][0])

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

            qs = qs.values_list('id', fields[0].fields_search[0][0])

            r += list(qs)
        r.sort(key=lambda x: x[1])
        return r
