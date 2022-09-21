
from django.apps.registry import apps

from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action

AudienciaApiViewSetConstrutor = ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('audiencia')
    ]
)
