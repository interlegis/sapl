from django.apps.registry import apps
from django.contrib.contenttypes.models import ContentType
from rest_framework.decorators import action
from rest_framework.response import Response

from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.base.models import Autor
from sapl.utils import models_with_gr_for_model


BaseApiViewSetConstrutor = ApiViewSetConstrutor.build_class(
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
    BaseApiViewSetConstrutor além do ofertado por
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
