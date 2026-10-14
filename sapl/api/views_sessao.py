
from django.apps.registry import apps
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action
from sapl.api.serializers import ChoiceSerializer,\
    SessaoPlenariaECidadaniaSerializer
from sapl.api.sessao_lote import SessaoLote
from sapl.api.sessao_painel import SessaoPainel
from sapl.sessao.models import SessaoPlenaria, ExpedienteSessao, \
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

    # As permissões são verificadas por item em SessaoLote, com as mesmas
    # regras dos endpoints individuais de cada model.
    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def lote(self, request, *args, **kwargs):
        """
        Grava em uma única requisição presenças da sessão, presenças da
        ordem do dia, votações, leituras e atualizações de matérias da
        sessão.
        Detalhes em docs/api-sessao-lote.md.
        """
        sessao = get_object_or_404(SessaoPlenaria, pk=kwargs['pk'])
        return Response(SessaoLote(sessao, request).processar(request.data))

    @action(detail=True)
    def painel(self, request, *args, **kwargs):
        """
        Devolve em uma única requisição tudo o que um painel eletrônico
        precisa para montar a sessão. Detalhes em docs/api-sessao-painel.md.
        """
        sessao = get_object_or_404(
            restringe_sessoes_visiveis(
                SessaoPlenaria.objects.select_related(
                    'tipo', 'sessao_legislativa', 'legislatura'), request.user),
            pk=kwargs['pk'])
        painel = SessaoPainel(sessao, request)
        sem_permissao = painel.models_sem_permissao()
        if sem_permissao:
            raise PermissionDenied('Sem permissão de leitura em: {}.'.format(
                ', '.join(sem_permissao)))
        return Response(painel.dados())


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
