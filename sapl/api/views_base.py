import logging

from django.apps.registry import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http.response import Http404
from rest_framework.decorators import action
from rest_framework.response import Response

from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.api.forms import AutoresPossiveisFilterSet
from sapl.api.serializers import ChoiceSerializer
from sapl.base.models import Autor, TipoAutor
from sapl.utils import models_with_gr_for_model, SaplGenericRelation


logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('contenttypes'),
        apps.get_app_config('base')
    ]
)


@customize(ContentType)
class _ContentTypeSet:
    http_method_names = ['get', 'head', 'options', 'trace']


@customize(Autor)
class _AutorViewSet:
    """
    Nesta customização do que foi criado em
    ApiViewSetConstrutor além do ofertado por
    rest_framework.viewsets.ModelViewSet, dentre outras customizações
    possíveis, foi adicionado as rotas referentes aos relacionamentos genéricos

    * padrão de ModelViewSet
        * /api/base/autor/       POST   - create
        * /api/base/autor/       GET    - list
        * /api/base/autor/{pk}/  GET    - detail
        * /api/base/autor/{pk}/  PUT    - update
        * /api/base/autor/{pk}/  PATCH  - partial_update
        * /api/base/autor/{pk}/  DELETE - destroy

    * rotas desta classe local criadas pelo método build local:
        * /api/base/autor/parlamentar
            devolve apenas autores que são parlamentares
        * /api/base/autor/comissao
            devolve apenas autores que são comissões
        * /api/base/autor/bloco
            devolve apenas autores que são blocos parlamentares
        * /api/base/autor/bancada
            devolve apenas autores que são bancadas parlamentares
        * /api/base/autor/frente
            devolve apenas autores que são Frene parlamentares
        * /api/base/autor/orgao
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

    @classmethod
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
            func.__name__ = func.kwargs['name']
            func.__model = _model

            setattr(cls, _model._meta.model_name, func)
        return cls

    @action(detail=False)
    def possiveis(self, request, *args, **kwargs):
        self.filterset_class = AutoresPossiveisFilterSet
        return self.list(request, *args, **kwargs)

    @action(detail=False)
    def provaveis(self, request, *args, **kwargs):

        self.get_queryset = self.provaveis__get_queryset

        self.filter_backends = []
        self.filterset_class = None
        self.serializer_class = ChoiceSerializer
        return self.list(request, *args, **kwargs)

    def provaveis__get_queryset(self):
        params = {'content_type__isnull': False}
        username = self.request.user.username
        tipo = ''
        try:
            tipo = int(self.request.GET.get('tipo', ''))
            if tipo:
                params['id'] = tipo
        except Exception as e:
            logger.error('user= ' + username + '. ' + str(e))
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
