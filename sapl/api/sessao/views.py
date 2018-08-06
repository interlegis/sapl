from rest_framework.filters import DjangoFilterBackend
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from sapl.api.sessao.serializers import SessaoPlenariaSerializer
from sapl.sessao.models import SessaoPlenaria


class SessaoPlenariaViewSet(ListModelMixin,
                            RetrieveModelMixin,
                            GenericViewSet):

    permission_classes = (AllowAny,)
    serializer_class = SessaoPlenariaSerializer
    queryset = SessaoPlenaria.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('data_inicio', 'data_fim', 'interativa')
