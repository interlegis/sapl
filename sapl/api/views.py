import logging
from calendar import timegm

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, JsonResponse
from django.utils.cache import get_conditional_response
from django.utils.http import http_date
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from drfautoapi.drfautoapi import ApiViewSetConstrutor

from sapl.base.models import AuditLog

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def recria_token(request, pk):
    Token.objects.filter(user_id=pk).delete()
    token = Token.objects.create(user_id=pk)

    return Response({"message": "Token recriado com sucesso!", "token": token.key})

class _RespostaCondicional(Exception):
    """Interrompe a requisição com a resposta condicional (304 ou 412)."""

    def __init__(self, response):
        super().__init__()
        self.response = response


class LastModifiedMixin:
    """ - Suporte a Last-Modified e a requisições condicionais
          (If-Modified-Since, If-Unmodified-Since) em ViewSets
        - A data vem do campo data_ultima_atualizacao ou ultima_edicao do
          model: no detalhe, a do objeto; na listagem, a mais recente entre
          os objetos retornados, levando em consideração o FilterSet
        - Retorna 304 Not Modified se o recurso não foi modificado

        - A checagem roda dentro do fluxo do DRF, depois de autenticação,
          permissões e throttling (initial), e usa o mesmo queryset da view
          (get_object no detalhe, filter_queryset na listagem). Assim, a
          data, o 304 e o 412 só existem para o que o usuário pode ver, e o
          Last-Modified só vai nas respostas de sucesso
        - Pode ser sobrescrito na customização do ViewSet caso necessário,
          redefinindo last_modified_func
        - Existe um exemplo de sobrescrita em sapl/api/views_materia.py
    """

    campos_last_modified = ('data_ultima_atualizacao', 'ultima_edicao')

    def initial(self, request, *args, **kwargs):
        self._last_modified = None

        # autenticação, permissões e throttling
        super().initial(request, *args, **kwargs)

        last_modified = None
        # Num método de escrita, só If-Unmodified-Since depende da data
        if (request.method in ('GET', 'HEAD') or
                'HTTP_IF_UNMODIFIED_SINCE' in request.META):
            try:
                data = self.last_modified_func(request, *args, **kwargs)
            except (APIException, Http404, PermissionDenied):
                # Filtro ou pk inválido, objeto oculto ou inexistente: a
                # view levanta o mesmo erro, e o DRF responde 400 ou 404.
                # As condições só valem para uma resposta de sucesso.
                return
            if data:
                last_modified = timegm(data.utctimetuple())

        self._last_modified = last_modified
        response = get_conditional_response(
            request, last_modified=last_modified)
        if response is not None:
            raise _RespostaCondicional(response)

    def handle_exception(self, exc):
        if isinstance(exc, _RespostaCondicional):
            return exc.response
        return super().handle_exception(exc)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(
            request, response, *args, **kwargs)

        last_modified = getattr(self, '_last_modified', None)
        sucesso = (200 <= response.status_code < 300 or
                   response.status_code == 304)
        if (last_modified and sucesso and
                request.method in ('GET', 'HEAD') and
                not response.has_header('Last-Modified')):
            response['Last-Modified'] = http_date(last_modified)
        return response

    def _eh_detalhe(self):
        return (self.lookup_url_kwarg or self.lookup_field) in self.kwargs

    def last_modified_func(self, request, *args, **kwargs):

        # tenta encontrar um dos campos para usar como last_modified
        field_name = next(
            (f.name for f in self.queryset.model._meta.get_fields()
             if f.name in self.campos_last_modified),
            None)

        # Retornando None. que indica 200 OK sem Last-Modified
        # Na prática, desativando o AuditLog como last_modified
        # Porém, mantendo a estrutura para possível uso futuro
        if not field_name:
            # sem campo definido para last_modified, usa AuditLog
            return None  # self.last_modified_func__auditlog(request, *args, **kwargs)

        if self._eh_detalhe():
            return getattr(self.get_object(), field_name)

        queryset = self.filter_queryset(self.get_queryset())
        return queryset.order_by(f'-{field_name}').values_list(
            field_name, flat=True)[:1].first()

    def last_modified_func__auditlog(self, request, *args, **kwargs):
        """ - Método alternativo para obter o last_modified baseado no
              AuditLog: o último registro do objeto, no detalhe, ou dos
              objetos retornados na listagem, levando em consideração o
              FilterSet
        """
        if self._eh_detalhe():
            object_ids = [self.get_object().pk]
        else:
            object_ids = self.filter_queryset(
                self.get_queryset()).values_list('pk', flat=True)

        try:
            return AuditLog.objects.filter(
                model_name=self.queryset.model._meta.model_name,
                object_id__in=object_ids
            ).order_by('-timestamp').values_list(
                'timestamp', flat=True)[:1].first()
        except Exception as e:
            logger.error(f"Erro ao obter last_modified: {e}")

        return None


class LastModifiedDecorator:
    """ - Decorator que o ApiViewSetConstrutor aplica às ViewSets que
          constrói: acrescenta o LastModifiedMixin
    """
    def __call__(self, cls):
        return type(cls.__name__, (LastModifiedMixin, cls), {
            '__module__': cls.__module__,
            '__qualname__': cls.__qualname__,
            '__doc__': cls.__doc__,
        })

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
