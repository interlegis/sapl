from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from sapl.api.serializers import SessaoPlenariaECidadaniaSerializer
from sapl.sessao.models import SessaoPlenaria


class SessaoPlenariaViewSet(ListModelMixin,
                            RetrieveModelMixin,
                            GenericViewSet):
    """
    Deprecated - Será eliminado na versão 3.2

    * TODO: 
        * eliminar endpoint, transferido para SaplApiViewSetConstrutor
            * /api/sessao-planaria -> /api/sessao/sessaoplenaria/ecidadania
            * /api/sessao-planaria/{pk} -> /api/sessao/sessaoplenaria/{pk}/ecidadania
        * verificar se ainda permanece necessidade desses endpoint's
    """

    permission_classes = (AllowAny,)
    serializer_class = SessaoPlenariaECidadaniaSerializer
    queryset = SessaoPlenaria.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('data_inicio', 'data_fim', 'interativa')
