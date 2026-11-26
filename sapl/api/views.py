import logging
from calendar import timegm

from django.conf import settings
from django.core.exceptions import FieldError, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Max, Q, Sum
from django.http import (Http404, HttpResponse, HttpResponseNotModified,
                         JsonResponse)
from django.utils.cache import get_conditional_response, patch_cache_control
from django.utils.http import http_date, parse_etags
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


def _sem_prefixo_fraco(etag):
    return etag[2:] if etag.startswith('W/') else etag


class LastModifiedMixin:
    """ - Suporte a requisições condicionais nas actions padrão das ViewSets
        - Detalhe (retrieve): Last-Modified com a data de atualização do
          objeto; If-Modified-Since responde 304 se ele não mudou
        - Listagem (list): ETag com a quantidade de objetos, a soma dos ids
          e a data mais recente, levando em consideração o FilterSet, e o
          Last-Modified com essa data. Na listagem, só o If-None-Match
          responde 304, porque a data mais recente não muda com exclusões,
          com objetos que saem do filtro nem com mudanças de visibilidade
        - Escritas (update, partial_update, destroy): If-Unmodified-Since
          responde 412 se o objeto mudou
        - Ficam de fora as actions customizadas e o ?expand=: o conteúdo
          vem de models relacionados, cujas alterações não mudam a data
        - A data vem do campo data_ultima_atualizacao, que o Django
          atualiza a cada save (auto_now). Se algum objeto da listagem
          tiver a data nula, a listagem fica sem validadores

        - A checagem roda dentro do fluxo do DRF, depois de autenticação,
          permissões e throttling (initial), e usa o mesmo queryset da view
          (get_object no detalhe, filter_queryset na listagem). Assim, os
          validadores, o 304 e o 412 só existem para o que o usuário pode
          ver, e os cabeçalhos só vão nas respostas de sucesso, com
          Cache-Control: private, no-cache, para o navegador sempre
          revalidar em vez de reaproveitar a resposta
        - Pode ser sobrescrito na customização do ViewSet caso necessário,
          redefinindo last_modified_func
        - Existe um exemplo de sobrescrita em sapl/api/views_materia.py
    """

    campo_last_modified = 'data_ultima_atualizacao'
    actions_de_leitura = ('list', 'retrieve')
    actions_de_escrita = ('update', 'partial_update', 'destroy')

    def initial(self, request, *args, **kwargs):
        self._last_modified = self._etag = None
        self._objeto = self._agregado = None

        # autenticação, permissões e throttling
        super().initial(request, *args, **kwargs)

        if not self._usa_validadores(request):
            return
        try:
            data = self.last_modified_func(request, *args, **kwargs)
            etag = self.etag_func(request, *args, **kwargs)
        except (APIException, Http404, PermissionDenied, FieldError,
                DjangoValidationError, TypeError, ValueError):
            # Filtro ou pk inválido, objeto oculto ou inexistente: a view
            # responde com o erro (400, 404 ou 500, se ela também falhar).
            # As condições só valem para uma resposta de sucesso.
            return

        self._last_modified = timegm(data.utctimetuple()) if data else None
        self._etag = etag

        if self.action == 'list':
            if etag and self._if_none_match_casa(request, etag):
                raise _RespostaCondicional(HttpResponseNotModified())
            return

        response = get_conditional_response(
            request, last_modified=self._last_modified)
        if response is not None:
            raise _RespostaCondicional(response)

    def handle_exception(self, exc):
        if isinstance(exc, _RespostaCondicional):
            return exc.response
        return super().handle_exception(exc)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(
            request, response, *args, **kwargs)

        sucesso = (200 <= response.status_code < 300 or
                   response.status_code == 304)
        if not sucesso or request.method not in ('GET', 'HEAD'):
            return response

        last_modified = getattr(self, '_last_modified', None)
        etag = getattr(self, '_etag', None)
        if last_modified and not response.has_header('Last-Modified'):
            response['Last-Modified'] = http_date(last_modified)
        if etag and not response.has_header('ETag'):
            response['ETag'] = etag
        if last_modified or etag:
            # Sem isso, o navegador pode reaproveitar a resposta sem
            # revalidar, por um tempo estimado a partir do Last-Modified
            patch_cache_control(response, private=True, no_cache=True)
        return response

    def get_object(self):
        # o objeto já buscado em last_modified_func, para não buscar de novo
        objeto, self._objeto = getattr(self, '_objeto', None), None
        if objeto is not None:
            return objeto
        return super().get_object()

    def _usa_validadores(self, request):
        if self.action in self.actions_de_leitura:
            return (request.method in ('GET', 'HEAD') and
                    'expand' not in request.query_params)
        if self.action in self.actions_de_escrita:
            return 'HTTP_IF_UNMODIFIED_SINCE' in request.META
        return False

    @staticmethod
    def _if_none_match_casa(request, etag):
        etags = parse_etags(request.META.get('HTTP_IF_NONE_MATCH', ''))
        if etags == ['*']:
            return True
        # comparação fraca (RFC 7232, seção 2.3.2)
        alvo = _sem_prefixo_fraco(etag)
        return any(_sem_prefixo_fraco(e) == alvo for e in etags)

    def _campo(self):
        campos = {f.name for f in self.queryset.model._meta.get_fields()}
        if self.campo_last_modified in campos:
            return self.campo_last_modified
        return None

    def _agregado_da_listagem(self):
        if self._agregado is None:
            campo = self._campo()
            queryset = self.filter_queryset(self.get_queryset())
            self._agregado = queryset.aggregate(
                total=Count('pk'), soma=Sum('pk'), data=Max(campo),
                nulos=Count('pk', filter=Q(**{f'{campo}__isnull': True})))
        return self._agregado

    def last_modified_func(self, request, *args, **kwargs):
        """Data do objeto, no detalhe, ou a mais recente da listagem."""
        # Retornando None. que indica 200 OK sem Last-Modified
        # Na prática, desativando o AuditLog como last_modified
        # Porém, mantendo a estrutura para possível uso futuro
        campo = self._campo()
        if not campo:
            # sem campo definido para last_modified, usa AuditLog
            return None  # self.last_modified_func__auditlog(request, *args, **kwargs)

        if self.action == 'list':
            agregado = self._agregado_da_listagem()
            return None if agregado['nulos'] else agregado['data']

        self._objeto = self.get_object()
        return getattr(self._objeto, campo)

    def etag_func(self, request, *args, **kwargs):
        """ETag da listagem; no detalhe, o Last-Modified basta."""
        if self.action != 'list' or not self._campo():
            return None
        agregado = self._agregado_da_listagem()
        if agregado['nulos']:
            return None
        data = agregado['data']
        return 'W/"{}-{}-{}"'.format(
            agregado['total'], agregado['soma'] or 0,
            int(data.timestamp() * 1000000) if data else 0)

    def last_modified_func__auditlog(self, request, *args, **kwargs):
        """ - Método alternativo para obter o last_modified baseado no
              AuditLog: o último registro do objeto, no detalhe, ou dos
              objetos retornados na listagem, levando em consideração o
              FilterSet
        """
        if self.action == 'list':
            object_ids = self.filter_queryset(
                self.get_queryset()).values_list('pk', flat=True)
        else:
            object_ids = [self.get_object().pk]

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
