
from django.apps.registry import apps
from rest_framework.decorators import action

from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action
from sapl.norma.models import NormaJuridica


ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('norma')
    ]
)
