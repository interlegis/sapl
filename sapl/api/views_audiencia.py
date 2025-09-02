from django.apps.registry import apps

from drfautoapi.drfautoapi import ApiViewSetConstrutor

AudienciaApiViewSetConstrutor = ApiViewSetConstrutor.build_class(
    [apps.get_app_config("audiencia")]
)
