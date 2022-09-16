import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView


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
