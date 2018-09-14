from rest_framework.filters import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from sapl.api.sessao.serializers import SessaoPlenariaOldSerializer,\
    SessaoPlenariaSerializer
from sapl.sessao.models import SessaoPlenaria


class SessaoPlenariaOldViewSet(ReadOnlyModelViewSet):

    permission_classes = (AllowAny,)
    serializer_class = SessaoPlenariaOldSerializer
    queryset = SessaoPlenaria.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('data_inicio', 'data_fim', 'interativa')


class SessaoPlenariaViewSet(ReadOnlyModelViewSet):

    permission_classes = (AllowAny,)
    serializer_class = SessaoPlenariaSerializer
    queryset = SessaoPlenaria.objects.all()
