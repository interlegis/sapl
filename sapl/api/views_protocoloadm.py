
from django.apps.registry import apps

from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action
from sapl.api.permissions import SaplModelPermissions
from sapl.base.models import AppConfig, DOC_ADM_OSTENSIVO
from sapl.protocoloadm.models import DocumentoAdministrativo, \
    DocumentoAcessorioAdministrativo, TramitacaoAdministrativo, Anexado


ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('protocoloadm')
    ]
)


@customize(DocumentoAdministrativo)
class _DocumentoAdministrativoViewSet:

    class DocumentoAdministrativoPermission(SaplModelPermissions):

        def has_permission(self, request, view):
            if request.method == 'GET':
                comportamento = AppConfig.attr('documentos_administrativos')
                if comportamento == DOC_ADM_OSTENSIVO:
                    return True
                    """
                    Diante da lógica implementada na manutenção de documentos
                    administrativos:
                    - Se o comportamento é doc adm ostensivo, deve passar pelo
                      teste de permissões sem avaliá-las
                    - se o comportamento é doc adm restritivo, deve passar pelo
                      teste de permissões avaliando-as
                    """
            return super().has_permission(request, view)

    permission_classes = (DocumentoAdministrativoPermission,)

    def get_queryset(self):
        """
        mesmo tendo passado pelo teste de permissões, deve ser filtrado,
        pelo campo restrito. Sendo este igual a True, disponibilizar apenas
        a um usuário conectado. Apenas isso, sem critérios outros de permissão,
        conforme implementado em DocumentoAdministrativoCrud
        """
        qs = super().get_queryset()

        if self.request.user.is_anonymous:
            qs = qs.exclude(restrito=True)
        return qs


@customize(DocumentoAcessorioAdministrativo)
class _DocumentoAcessorioAdministrativoViewSet:

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission,)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.is_anonymous or 'protocoloadm.change_documentoacessorioadministrativo' not in user.get_all_permissions():
#        if self.request.user.is_anonymous:
            qs = qs.exclude(documento__restrito=True)
            qs = qs.exclude(restrito=True)
        return qs


@customize(TramitacaoAdministrativo)
class _TramitacaoAdministrativoViewSet:
    # TODO: Implementar regras de manutenção das post, put, patch
    # tramitacação de adm possui regras previstas de limitação de origem
    # destino

    http_method_names = ['get', 'head', 'options', 'trace']

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission,)

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous:
            qs = qs.exclude(documento__restrito=True)
        return qs


@customize(Anexado)
class _AnexadoViewSet:
    # TODO: Implementar regras de manutenção post, put, patch
    # anexado deve possuir controle que impeça anexação cíclica
    http_method_names = ['get', 'head', 'options', 'trace']

    permission_classes = (
        _DocumentoAdministrativoViewSet.DocumentoAdministrativoPermission,)

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_anonymous:
            qs = qs.exclude(documento__restrito=True)
        return qs
