
from django.apps.registry import apps
from rest_framework.decorators import action
from rest_framework.response import Response

from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action
from sapl.api.permissions import PodeEnviarPautaAoPainelExterno
from sapl.api.serializers import ChoiceSerializer,\
    SessaoPlenariaECidadaniaSerializer
from sapl.sessao import painel_externo
from sapl.sessao.models import SessaoPlenaria, ExpedienteSessao,\
    restringe_sessoes_visiveis
from sapl.utils import choice_anos_com_sessaoplenaria


ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('sessao')
    ]
)


@customize(SessaoPlenaria)
class _SessaoPlenariaViewSet:

    def get_queryset(self):
        qs = super().get_queryset()
        # actions com wrapper_queryset_response_for_drf_action trocam o model
        if qs.model is SessaoPlenaria:
            qs = restringe_sessoes_visiveis(qs, self.request.user)
        return qs

    @action(detail=False)
    def years(self, request, *args, **kwargs):
        years = choice_anos_com_sessaoplenaria()

        serializer = ChoiceSerializer(years, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def expedientes(self, request, *args, **kwargs):
        self.get_object()
        return self.get_expedientes()

    @wrapper_queryset_response_for_drf_action(model=ExpedienteSessao)
    def get_expedientes(self):
        return self.get_queryset().filter(sessao_plenaria_id=self.kwargs['pk'])

    @action(detail=True)
    def ecidadania(self, request, *args, **kwargs):
        self.serializer_class = SessaoPlenariaECidadaniaSerializer
        return self.retrieve(request, *args, **kwargs)

    @action(detail=False, url_path='ecidadania')
    def ecidadania_list(self, request, *args, **kwargs):
        self.serializer_class = SessaoPlenariaECidadaniaSerializer
        return self.list(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='materias/enviar',
            permission_classes=[PodeEnviarPautaAoPainelExterno])
    def materias_enviar(self, request, *args, **kwargs):
        # URL e chave vêm só de AppConfig: o corpo da requisição é ignorado
        resultado = painel_externo.enviar_pauta(self.get_object(), request)
        return Response(resultado._asdict(),
                        status=200 if resultado.ok else 502)


class _RestringeSessoesVisiveisMixin:

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            return qs
        return qs.filter(sessao_plenaria__in=restringe_sessoes_visiveis(
            SessaoPlenaria.objects.all(), self.request.user))


for _model in apps.get_app_config('sessao').get_models():
    if _model is not SessaoPlenaria and any(
            f.name == 'sessao_plenaria' for f in _model._meta.fields):
        customize(_model)(type('_%sViewSet' % _model.__name__,
                               (_RestringeSessoesVisiveisMixin,), {}))
