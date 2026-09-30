import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from drfautoapi.drfautoapi import ApiViewSetConstrutor
from django.views.decorators.http import condition as django_condition

from sapl.base.models import AuditLog

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def recria_token(request, pk):
    Token.objects.filter(user_id=pk).delete()
    token = Token.objects.create(user_id=pk)

    return Response({"message": "Token recriado com sucesso!", "token": token.key})

class LastModifiedDecorator:
    """ - Decorator para adicionar suporte a Last-Modified em ViewSets
        - Baseado em django.views.decorators.http.condition

        - Por padrão utiliza o AuditLog para determinar a data do last_modified
        - Pode ser sobrescrito na customização do ViewSet caso necessário
        - Existe um exemplo de sobrescrita em sapl/api/views_materia.py

        - Devolve Last-Modified baseado no timestamp do último AuditLog
        - Se for uma listagem, considera o último AuditLog de todos os objetos
          retornados na listagem levando em consideração resultado de FilterSet.
        - Retorna 304 Not Modified se o recurso não foi modificado
    """
    def __call__(self, cls):

        original_dispatch = cls.dispatch
        self.model = cls.queryset.model

        def wrapped_dispatch(view, request, *args, **kwargs):
            drf_request = request
            wsgi_request = view.initialize_request(request, *args, **kwargs)

            last_modified_func = self.last_modified_func if not hasattr(view, 'last_modified_func') else view.last_modified_func

            def patched_viewset_method(*_args, **_kwargs):
                return original_dispatch(view, drf_request, *args, **kwargs)

            django_decorator = django_condition(last_modified_func=last_modified_func)
            decorated_viewset_method = django_decorator(patched_viewset_method)
            return decorated_viewset_method(wsgi_request, *args, view=view, **kwargs)

        cls.dispatch = wrapped_dispatch
        return cls

    def last_modified_func(self, request, *args, **kwargs):

        default_fields_for_timestamp = (
            'data_ultima_atualizacao',
            'ultima_edicao'
        )

        # tenta encontrar um dos campos acima para usar como last_modified
        fields = tuple(
            filter(
                lambda f: f in default_fields_for_timestamp,
                map(
                    lambda f: f.name, self.model._meta.get_fields()
                )
            )
        )
        field_name = fields[0] if fields else None

        # Retornando None. que indica para o decorator retornar 200 OK sem Last-Modified
        # Na prática, desativando o AuditLog como last_modified
        # Porém, mantendo a estrutura para possível uso futuro
        if not field_name:
            # sem campo definido para last_modified, usa AuditLog
            return None # self.last_modified_func__auditlog(request, *args, **kwargs)

        pk = kwargs.get('pk', None)
        if pk:
            return self.model.objects.filter(pk=pk).values_list(field_name, flat=True)[:1].first()

        view = kwargs.get('view', None)

        if view:
            queryset = view.get_queryset()
            for backend in list(view.filter_backends):
                queryset = backend().filter_queryset(request, queryset, view)
        else:
            queryset = self.model.objects.all()

        timestamp = queryset.order_by(f'-{field_name}').values_list(field_name, flat=True)[:1].first()
        return timestamp

    def last_modified_func__auditlog(self, request, *args, **kwargs):
        """ - Método padrão para obter o last_modified baseado no AuditLog
            - Pode ser sobrescrito na customização do ViewSet caso necessário
            - Existe um exemplo de sobrescrita em sapl/api/views_materia.py
        """
        try:
            if 'pk' in kwargs:
                obj_id = kwargs['pk']
                last_log = AuditLog.objects.filter(
                    model_name=self.model._meta.model_name,
                    object_id=obj_id
                ).order_by('-timestamp').values_list('timestamp', flat=True)[:1].first()
            else:
                view = kwargs.get('view', None)
                if view:
                    for backend in list(view.filter_backends):
                        queryset = backend().filter_queryset(request, view.queryset, view)

                    if queryset.exists():
                        last_log = AuditLog.objects.filter(
                            model_name=self.model._meta.model_name,
                            object_id__in=queryset.values_list('pk', flat=True)
                        ).order_by('-timestamp').values_list('timestamp', flat=True)[:1].first()
                    else:
                        last_log = None
                else:
                    last_log = AuditLog.objects.filter(
                        model_name=self.model._meta.model_name,
                        object_id__in=self.model.objects.values_list('pk', flat=True)
                    ).order_by('-timestamp').values_list('timestamp', flat=True)[:1].first()

            if last_log:
                return last_log

        except Exception as e:
            logger.error(f"Erro ao obter last_modified: {e}")

        return None

SaplApiViewSetConstrutor = ApiViewSetConstrutor
SaplApiViewSetConstrutor.last_modified_class(LastModifiedDecorator)
SaplApiViewSetConstrutor.import_modules([
    'sapl.api.views_audiencia',
    'sapl.api.views_base',
    'sapl.api.views_comissoes',
    'sapl.api.views_compilacao',
    'sapl.api.views_materia',
    'sapl.api.views_norma',
    'sapl.api.views_painel',
    'sapl.api.views_parlamentares',
    'sapl.api.views_protocoloadm',
    'sapl.api.views_sessao',
])


"""
1. ApiViewSetConstrutor constroi uma rest_framework.viewsets.ModelViewSet
     para todos os models de todas as app_configs passadas no list
2. Define DjangoFilterBackend como ferramenta de filtro dos campos
3. Define Serializer como a seguir:
    3.1   - Define um Serializer genérico para cada módel
    3.1.1 - se existir um DEFAULT_SERIALIZER_MODULE em settings,
            recupera Serializer customizados no módulo DEFAULT_SERIALIZER_MODULE
    3.2 - Para todo model é opcional a existência de {model}Serializer.
          Caso não seja definido um Serializer customizado, utiliza-se o genérico
    3.3 - Caso exista GLOBAL_SERIALIZER_MIXIN definido,
          utiliza este Serializer para construir o genérico de 3.1
4. Define um FilterSet como a seguir:
    4.1 -   Define um FilterSet genérico para cada módel
    4.1.1 - se existir um DEFAULT_FILTER_MODULE em settings,
            recupera o FilterSet customizado no módulo DEFAULT_FILTER_MODULE
    4.2 - Para todo model é opcional a existência de {model}FilterSet.
          Caso não seja definido um FilterSet customizado, utiliza-se o genérico
    4.3 - Caso exista GLOBAL_FILTERSET_MIXIN definido,
          utiliza este FilterSet para construir o genérico de 4.1
    4.4 - Caso não exista GLOBAL_FILTERSET_MIXIN, será aplicado
          drfautoapi.drjautoapi.ApiFilterSetMixin que inclui parametro para:
          - order_by: através do parâmetro "o"
          - amplia os lookups aceitos pelo FilterSet default
            para os aceitos pelo django sem a necessidade de criar
            fields específicos em um FilterSet customizado.

5. ApiViewSetConstrutor não cria padrões e/ou exige conhecimento alem dos
    exigidos pela DRF.

6. As rotas são criadas seguindo nome da app e nome do model
    http://localhost:9000/api/{applabel}/{model_name}/
    e seguem as variações definidas em:
    https://www.django-rest-framework.org/api-guide/routers/#defaultrouter


**ApiViewSetConstrutor._built_sets** é um dict de dicts de models conforme:
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
