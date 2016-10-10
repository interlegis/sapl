from django.http import Http404
from rest_framework import mixins, viewsets
from rest_framework.generics import ListAPIView, GenericAPIView,\
    get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from sapl.api.serializers import ChoiceSerializer
from sapl.base.models import Autor, TipoAutor


class TipoAutorContentOfModelContentTypeView(ListAPIView):
    serializer_class = ChoiceSerializer
    permission_classes = (AllowAny,)
    queryset = TipoAutor.objects.all()
    model = TipoAutor
    pagination_class = None

    def get_queryset(self):
        queryset = ModelViewSet.get_queryset(self)
        if not self.kwargs['pk']:
            return queryset

        obj = get_object_or_404(queryset, pk=self.kwargs['pk'])

        if not obj.content_type:
            raise Http404

        q = self.request.GET.get('q', None)

        if not q:
            return []
        else:
            return obj.content_type.model_class().objects.filter(
                nome__icontains=q)[:10]
