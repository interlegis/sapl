
from django.apps.registry import apps
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.status import HTTP_201_CREATED, HTTP_409_CONFLICT
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

    _MAX_RETRIES_NUMERO = 3

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = dict(request.data)
        tipo = data.get('tipo', None)
        numero = data.get('numero', None)
        ano = data.get('ano', None)

        if tipo and not numero:
            # Número não fornecido pelo cliente: auto-gerar próximo disponível.
            # select_for_update() em get_proximo_numero previne race conditions.
            # Retry como camada extra de segurança contra IntegrityError residual.
            for tentativa in range(self._MAX_RETRIES_NUMERO):
                try:
                    with transaction.atomic():
                        numero_gerado, ano_gerado = MateriaLegislativa.get_proximo_numero(
                            tipo=tipo, ano=ano
                        )
                        data['numero'] = numero_gerado
                        data['ano'] = ano_gerado

                        serializer = self.get_serializer(data=data)
                        serializer.is_valid(raise_exception=True)
                        self.perform_create(serializer)
                        headers = self.get_success_headers(serializer.data)
                        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)
                except IntegrityError:
                    if tentativa == self._MAX_RETRIES_NUMERO - 1:
                        return Response(
                            {'detail': 'Não foi possível gerar um número único após '
                                       '%d tentativas. Tente novamente.' % self._MAX_RETRIES_NUMERO},
                            status=HTTP_409_CONFLICT
                        )
                    continue

        # Número fornecido pelo cliente (ou tipo ausente):
        # respeitar os dados enviados. Se houver conflito de unicidade,
        # retornar erro explícito em vez de sobrescrever silenciosamente.
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                self.perform_create(serializer)
        except IntegrityError:
            return Response(
                {'numero': [
                    'O número %s já está em uso para este tipo/ano. '
                    'Remova o campo "numero" para auto-gerar o próximo disponível.' % numero
                ]},
                status=HTTP_409_CONFLICT
            )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['GET'])
    def ultima_tramitacao(self, request, *args, **kwargs):

        materia = self.get_object()
        if not materia.tramitacao_set.exists():
            return Response({})

        ultima_tramitacao = materia.tramitacao_set.order_by(
            '-data_tramitacao', '-id').first()

        serializer_class = ApiViewSetConstrutor.get_viewset_for_model(
            Tramitacao).serializer_class(ultima_tramitacao)

        return Response(serializer_class.data)

    @action(detail=True, methods=['GET'])
    def anexadas(self, request, *args, **kwargs):
        self.queryset = self.get_object().anexadas.all()
        return self.list(request, *args, **kwargs)

"""
        O próprio decorator LastModifiedDecorator já implementa o método last_modified_func que atende o caso
        específico de MateriaLegislativa, baseado no campo data_ultima_atualizacao.
        Portanto, não há necessidade de reimplementar este método aqui. Mas segue o código comentado
        para referência futura caso necessário e como exemplo de implementação customizada que sobrescreve
        o comportamento padrão do decorator.

    def last_modified_func(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        if pk:
            return MateriaLegislativa.objects.filter(pk=pk).values_list('data_ultima_atualizacao', flat=True)[:1].first()

        queryset = self.get_queryset()
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(request, self.queryset, self)

        timestamp = queryset.order_by('-data_ultima_atualizacao').values_list('data_ultima_atualizacao', flat=True)[:1].first()
        return timestamp
"""

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
