from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from rest_framework.generics import ListAPIView
from rest_framework.permissions import (IsAuthenticated, AllowAny)
from rest_framework.response import Response
from rest_framework.views import APIView

from sapl.api.serializers import ModelChoiceSerializer
from sapl.rules.apps import AppConfig


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


class TimeRefreshDatabaseView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        return Response({'last_global_refresh_time': apps.get_app_config('rules').time_refresh})
