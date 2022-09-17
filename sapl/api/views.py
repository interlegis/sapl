import logging

from django.apps.registry import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from drfautoapi.drfautoapi import customize, ApiViewSetConstrutor, \
    wrapper_queryset_response_for_drf_action, \
    BusinessRulesNotImplementedMixin
from sapl.api.permissions import SaplModelPermissions
from sapl.api.serializers import ParlamentarSerializerVerbose, \
    ParlamentarSerializerPublic, ChoiceSerializer
from sapl.base.models import Autor, AppConfig, DOC_ADM_OSTENSIVO
from sapl.materia.models import Proposicao, TipoMateriaLegislativa, \
    MateriaLegislativa, Tramitacao
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Mandato, Legislatura
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import DocumentoAdministrativo, \
    DocumentoAcessorioAdministrativo, TramitacaoAdministrativo, Anexado
from sapl.sessao.models import SessaoPlenaria, ExpedienteSessao
from sapl.utils import models_with_gr_for_model, choice_anos_com_sessaoplenaria


logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def recria_token(request, pk):
    Token.objects.filter(user_id=pk).delete()
    token = Token.objects.create(user_id=pk)

    return Response({"message": "Token recriado com sucesso!", "token": token.key})


class AppVersionView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        content = {
            'name': 'SAPL',
            'description': 'Sistema de Apoio ao Processo Legislativo',
            'version': settings.SAPL_VERSION,
            'user': request.user.username,
            'is_authenticated': request.user.is_authenticated,
        }
        return Response(content)


SaplApiViewSetConstrutor = ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('contenttypes')
    ] + [
        apps.get_app_config(n[5:]) for n in settings.SAPL_APPS
    ]
)
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


@customize(ContentType)
class _ContentTypeSet:
    http_method_names = ['get', 'head', 'options', 'trace']


@customize(Parlamentar)
class _ParlamentarViewSet:

    class ParlamentarPermission(SaplModelPermissions):

        def has_permission(self, request, view):
            if request.method == 'GET':
                return True
            else:
                perm = super().has_permission(request, view)
                return perm

    permission_classes = (ParlamentarPermission,)

    def get_serializer(self, *args, **kwargs):
        if not self.request.user.has_perm('parlamentares.add_parlamentar'):
            self.serializer_class = ParlamentarSerializerPublic
        return super().get_serializer(*args, **kwargs)

    @action(detail=True)
    def proposicoes(self, request, *args, **kwargs):
        """
        Lista de proposições públicas de parlamentar específico

        :param int id: - Identificador do parlamentar que se quer recuperar as proposições
        :return: uma lista de proposições
        """
        # /api/parlamentares/parlamentar/{id}/proposicoes/
        # recupera proposições enviadas e incorporadas do parlamentar
        # deve coincidir com
        # /parlamentar/{pk}/proposicao

        return self.get_proposicoes(**kwargs)

    @wrapper_queryset_response_for_drf_action(model=Proposicao)
    def get_proposicoes(self, **kwargs):

        return self.get_queryset().filter(
            data_envio__isnull=False,
            data_recebimento__isnull=False,
            cancelado=False,
            autor__object_id=kwargs['pk'],
            autor__content_type=ContentType.objects.get_for_model(Parlamentar)
        )

    @action(detail=False, methods=['GET'])
    def search_parlamentares(self, request, *args, **kwargs):
        nome = request.query_params.get('nome_parlamentar', '')
        parlamentares = Parlamentar.objects.filter(
            nome_parlamentar__icontains=nome)
        serializer_class = ParlamentarSerializerVerbose(
            parlamentares, many=True, context={'request': request})
        return Response(serializer_class.data)


@customize(Legislatura)
class _LegislaturaViewSet:

    @action(detail=True)
    def parlamentares(self, request, *args, **kwargs):

        def get_serializer_context():
            return {
                'request': self.request, 'legislatura': kwargs['pk']
            }

        def get_serializer_class():
            return ParlamentarSerializerVerbose

        self.get_serializer_context = get_serializer_context
        self.get_serializer_class = get_serializer_class

        return self.get_parlamentares()

    @wrapper_queryset_response_for_drf_action(model=Parlamentar)
    def get_parlamentares(self):

        try:
            legislatura = Legislatura.objects.get(pk=self.kwargs['pk'])
        except ObjectDoesNotExist:
            return Response("")

        filter_params = {
            'legislatura': legislatura,
            'data_inicio_mandato__gte': legislatura.data_inicio,
            'data_fim_mandato__lte': legislatura.data_fim,
        }

        mandatos = Mandato.objects.filter(
            **filter_params).order_by('-data_inicio_mandato')

        parlamentares = self.get_queryset().filter(
            mandato__in=mandatos).distinct()

        return parlamentares


@customize(Proposicao)
class _ProposicaoViewSet:
    """
    list:
        Retorna lista de Proposições

        * Permissões:

            * Usuário Dono:
                * Pode listar todas suas Proposições

            * Usuário Conectado ou Anônimo:
                * Pode listar todas as Proposições incorporadas

    retrieve:
        Retorna uma proposição passada pelo 'id'

        * Permissões:

            * Usuário Dono:
                * Pode recuperar qualquer de suas Proposições

            * Usuário Conectado ou Anônimo:
                * Pode recuperar qualquer das proposições incorporadas

    """

    class ProposicaoPermission(SaplModelPermissions):

        def has_permission(self, request, view):
            if request.method == 'GET':
                return True
                # se a solicitação é list ou detail, libera o teste de permissão
                # e deixa o get_queryset filtrar de acordo com a regra de
                # visibilidade das proposições, ou seja:
                # 1. proposição incorporada é proposição pública
                # 2. não incorporada só o autor pode ver
            else:
                perm = super().has_permission(request, view)
                return perm
                # não é list ou detail, então passa pelas regras de permissão e,
                # depois disso ainda passa pelo filtro de get_queryset

    permission_classes = (ProposicaoPermission,)

    def get_queryset(self):
        qs = super().get_queryset()

        q = Q(data_recebimento__isnull=False, object_id__isnull=False)
        if not self.request.user.is_anonymous:

            autor_do_usuario_logado = self.request.user.autor_set.first()

            # se usuário logado é operador de algum autor
            if autor_do_usuario_logado:
                q = Q(autor=autor_do_usuario_logado)

            # se é operador de protocolo, ve qualquer coisa enviada
            if self.request.user.has_perm('protocoloadm.list_protocolo'):
                q = Q(data_envio__isnull=False) | Q(
                    data_devolucao__isnull=False)

        qs = qs.filter(q)
        return qs


@customize(MateriaLegislativa)
class _MateriaLegislativaViewSet:

    class Meta:
        ordering = ['-ano', 'tipo', 'numero']

    @action(detail=True, methods=['GET'])
    def ultima_tramitacao(self, request, *args, **kwargs):

        materia = self.get_object()
        if not materia.tramitacao_set.exists():
            return Response({})

        ultima_tramitacao = materia.tramitacao_set.order_by(
            '-data_tramitacao', '-id').first()

        serializer_class = SaplApiViewSetConstrutor.get_class_for_model(
            Tramitacao).serializer_class(ultima_tramitacao)

        return Response(serializer_class.data)

    @action(detail=True, methods=['GET'])
    def anexadas(self, request, *args, **kwargs):
        self.queryset = self.get_object().anexadas.all()
        return self.list(request, *args, **kwargs)


@customize(TipoMateriaLegislativa)
class _TipoMateriaLegislativaViewSet:

    @action(detail=True, methods=['POST'])
    def change_position(self, request, *args, **kwargs):
        result = {
            'status': 200,
            'message': 'OK'
        }
        d = request.data
        if 'pos_ini' in d and 'pos_fim' in d:
            if d['pos_ini'] != d['pos_fim']:
                pk = kwargs['pk']
                TipoMateriaLegislativa.objects.reposicione(pk, d['pos_fim'])

        return Response(result)


@customize(DocumentoAdministrativo)
class _DocumentoAdministrativoViewSet:

    class DocumentoAdministrativoPermission(SaplModelPermissions):

        def has_permission(self, request, view):
            if request.method == 'GET':
                comportamento = AppConfig.attr('documentos_administrativos')
                if comportamento == DOC_ADM_OSTENSIVO:
                    return True
                    """
                    Diante da lógica implementada na manutenção de documentos
                    administrativos:
                    - Se o comportamento é doc adm ostensivo, deve passar pelo
                      teste de permissões sem avaliá-las
                    - se o comportamento é doc adm restritivo, deve passar pelo
                      teste de permissões avaliando-as
                    """
            return super().has_permission(request, view)

    permission_classes = (DocumentoAdministrativoPermission,)

    def get_queryset(self):
        """
        mesmo tendo passado pelo teste de permissões, deve ser filtrado,
        pelo campo restrito. Sendo este igual a True, disponibilizar apenas
        a um usuário conectado. Apenas isso, sem critérios outros de permissão,
        conforme implementado em DocumentoAdministrativoCrud
        """
        qs = super().get_queryset()

        if self.request.user.is_anonymous:
            qs = qs.exclude(restrito=True)
        return qs


@customize(DocumentoAcessorioAdministrativo)
class _DocumentoAcessorioAdministrativoViewSet:

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission,)

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous:
            qs = qs.exclude(documento__restrito=True)
        return qs


@customize(TramitacaoAdministrativo)
class _TramitacaoAdministrativoViewSet(BusinessRulesNotImplementedMixin):
    # TODO: Implementar regras de manutenção das tramitações de docs adms

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission,)

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous:
            qs = qs.exclude(documento__restrito=True)
        return qs


@customize(Anexado)
class _AnexadoViewSet(BusinessRulesNotImplementedMixin):

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission,)

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous:
            qs = qs.exclude(documento__restrito=True)
        return qs


@customize(SessaoPlenaria)
class _SessaoPlenariaViewSet:

    @action(detail=False)
    def years(self, request, *args, **kwargs):
        years = choice_anos_com_sessaoplenaria()

        serializer = ChoiceSerializer(years, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def expedientes(self, request, *args, **kwargs):
        return self.get_expedientes()

    @wrapper_queryset_response_for_drf_action(model=ExpedienteSessao)
    def get_expedientes(self):
        return self.get_queryset().filter(sessao_plenaria_id=self.kwargs['pk'])


@customize(NormaJuridica)
class _NormaJuridicaViewset:

    @action(detail=False, methods=['GET'])
    def destaques(self, request, *args, **kwargs):
        self.queryset = self.get_queryset().filter(norma_de_destaque=True)
        return self.list(request, *args, **kwargs)


@customize(Autor)
class _AutorViewSet:
    # Customização para AutorViewSet com implementação de actions específicas
    """
    Nesta customização do que foi criado em
    SaplApiViewSetConstrutor além do ofertado por
    rest_framework.viewsets.ModelViewSet, dentre outras customizações
    possíveis, foi adicionado as rotas referentes aos relacionamentos genéricos

    * padrão de ModelViewSet
        /api/base/autor/       POST   - create
        /api/base/autor/       GET    - list
        /api/base/autor/{pk}/  GET    - detail
        /api/base/autor/{pk}/  PUT    - update
        /api/base/autor/{pk}/  PATCH  - partial_update
        /api/base/autor/{pk}/  DELETE - destroy

    * rotas desta classe local criadas pelo método build:
        /api/base/autor/parlamentar
            devolve apenas autores que são parlamentares
        /api/base/autor/comissao
            devolve apenas autores que são comissões
        /api/base/autor/bloco
            devolve apenas autores que são blocos parlamentares
        /api/base/autor/bancada
            devolve apenas autores que são bancadas parlamentares
        /api/base/autor/frente
            devolve apenas autores que são Frene parlamentares
        /api/base/autor/orgao
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
