import logging

from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from drfautoapi.drfautoapi import ApiViewSetConstrutor

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


SaplApiViewSetConstrutor = ApiViewSetConstrutor
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
