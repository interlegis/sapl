from django.contrib.contenttypes.models import ContentType
from rest_framework.filters import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import (AllowAny, IsAuthenticated)
from rest_framework.viewsets import GenericViewSet

from sapl.api.serializers import (
    MateriaLegislativaSerializer,
    ModelChoiceSerializer,
    SessaoPlenariaSerializer)
from sapl.materia.models import MateriaLegislativa
from sapl.sessao.models import SessaoPlenaria


class ModelChoiceView(ListAPIView):

    # FIXME aplicar permissão correta de usuário
    permission_classes = (IsAuthenticated,)
    serializer_class = ModelChoiceSerializer

    def get(self, request, *args, **kwargs):
        self.model = ContentType.objects.get_for_id(
            self.kwargs['content_type']).model_class()

        pagination = request.GET.get('pagination', '')

        if pagination == 'False':
            self.pagination_class = None

        return ListAPIView.get(self, request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.all()


class MateriaLegislativaViewSet(ListModelMixin,
                                RetrieveModelMixin,
                                GenericViewSet):

    permission_classes = (IsAuthenticated,)
    serializer_class = MateriaLegislativaSerializer
    queryset = MateriaLegislativa.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('numero', 'ano', 'tipo', )


class SessaoPlenariaViewSet(ListModelMixin,
                            RetrieveModelMixin,
                            GenericViewSet):

    permission_classes = (AllowAny,)
    serializer_class = SessaoPlenariaSerializer
    queryset = SessaoPlenaria.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('data_inicio', 'data_fim', 'interativa')
