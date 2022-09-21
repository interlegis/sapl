
from django.apps.registry import apps
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response

from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action
from sapl.api.permissions import SaplModelPermissions
from sapl.materia.models import TipoMateriaLegislativa, Tramitacao,\
    MateriaLegislativa, Proposicao


ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('materia')
    ]
)


@customize(Proposicao)
class _ProposicaoViewSet:
    """
    list:
        Retorna lista de Proposições

        * Permissões:

            * Usuário Dono:
                * Pode listar todas suas Proposições

            * Usuário Conectado ou Anônimo:
                * Pode listar todas as Proposições incorporadas

    retrieve:
        Retorna uma proposição passada pelo 'id'

        * Permissões:

            * Usuário Dono:
                * Pode recuperar qualquer de suas Proposições

            * Usuário Conectado ou Anônimo:
                * Pode recuperar qualquer das proposições incorporadas

    """

    class ProposicaoPermission(SaplModelPermissions):

        def has_permission(self, request, view):
            if request.method == 'GET':
                return True
                # se a solicitação é list ou detail, libera o teste de permissão
                # e deixa o get_queryset filtrar de acordo com a regra de
                # visibilidade das proposições, ou seja:
                # 1. proposição incorporada é proposição pública
                # 2. não incorporada só o autor pode ver
            else:
                perm = super().has_permission(request, view)
                return perm
                # não é list ou detail, então passa pelas regras de permissão e,
                # depois disso ainda passa pelo filtro de get_queryset

    permission_classes = (ProposicaoPermission,)

    def get_queryset(self):
        qs = super().get_queryset()

        q = Q(data_recebimento__isnull=False, object_id__isnull=False)
        if not self.request.user.is_anonymous:

            autor_do_usuario_logado = self.request.user.autor_set.first()

            # se usuário logado é operador de algum autor
            if autor_do_usuario_logado:
                q = Q(autor=autor_do_usuario_logado)

            # se é operador de protocolo, ve qualquer coisa enviada
            if self.request.user.has_perm('protocoloadm.list_protocolo'):
                q = Q(data_envio__isnull=False) | Q(
                    data_devolucao__isnull=False)

        qs = qs.filter(q)
        return qs


@customize(MateriaLegislativa)
class _MateriaLegislativaViewSet:

    class Meta:
        ordering = ['-ano', 'tipo', 'numero']

    @action(detail=True, methods=['GET'])
    def ultima_tramitacao(self, request, *args, **kwargs):

        materia = self.get_object()
        if not materia.tramitacao_set.exists():
            return Response({})

        ultima_tramitacao = materia.tramitacao_set.order_by(
            '-data_tramitacao', '-id').first()

        serializer_class = MateriaApiViewSetConstrutor.get_viewset_for_model(
            Tramitacao).serializer_class(ultima_tramitacao)

        return Response(serializer_class.data)

    @action(detail=True, methods=['GET'])
    def anexadas(self, request, *args, **kwargs):
        self.queryset = self.get_object().anexadas.all()
        return self.list(request, *args, **kwargs)


@customize(TipoMateriaLegislativa)
class _TipoMateriaLegislativaViewSet:

    @action(detail=True, methods=['POST'])
    def change_position(self, request, *args, **kwargs):
        result = {
            'status': 200,
            'message': 'OK'
        }
        d = request.data
        if 'pos_ini' in d and 'pos_fim' in d:
            if d['pos_ini'] != d['pos_fim']:
                pk = kwargs['pk']
                TipoMateriaLegislativa.objects.reposicione(pk, d['pos_fim'])

        return Response(result)
