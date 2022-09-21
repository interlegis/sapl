
from django.apps.registry import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import action
from rest_framework.response import Response

from drfautoapi.drfautoapi import customize, ApiViewSetConstrutor, \
    wrapper_queryset_response_for_drf_action

from sapl.api.permissions import SaplModelPermissions
from sapl.api.serializers import ParlamentarSerializerVerbose, \
    ParlamentarSerializerPublic
from sapl.materia.models import Proposicao
from sapl.parlamentares.models import Mandato, Legislatura
from sapl.parlamentares.models import Parlamentar

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('parlamentares')
    ]
)


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
