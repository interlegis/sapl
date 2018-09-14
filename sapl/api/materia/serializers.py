
from rest_framework.filters import DjangoFilterBackend
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from sapl.api.materia.views import MateriaLegislativaSerializer
from sapl.materia.models import MateriaLegislativa


class MateriaLegislativaViewSet(ListModelMixin,
                                RetrieveModelMixin,
                                GenericViewSet):

    permission_classes = (IsAuthenticated,)
    serializer_class = MateriaLegislativaSerializer
    queryset = MateriaLegislativa.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('numero', 'ano', 'tipo', )
