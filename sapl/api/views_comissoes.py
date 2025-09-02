from django.apps.registry import apps
from rest_framework.decorators import action

from drfautoapi.drfautoapi import (
    ApiViewSetConstrutor,
    customize,
    wrapper_queryset_response_for_drf_action,
)
from sapl.comissoes.models import Comissao
from sapl.materia.models import MateriaEmTramitacao

ApiViewSetConstrutor.build_class([apps.get_app_config("comissoes")])


@customize(Comissao)
class _ComissaoViewSet:
    @action(detail=True)
    def materiaemtramitacao(self, request, *args, **kwargs):
        return self.get_materiaemtramitacao(**kwargs)

    @wrapper_queryset_response_for_drf_action(model=MateriaEmTramitacao)
    def get_materiaemtramitacao(self, **kwargs):
        return self.get_queryset().filter(
            unidade_tramitacao_atual__comissao=kwargs["pk"],
        )
