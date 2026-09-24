import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sapl.settings")
django.setup()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.http import AsgiHandler  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from django.urls import path  # noqa: E402

from sapl.painel.consumers import PainelConsumer  # noqa: E402

application = ProtocolTypeRouter({
    "http": AsgiHandler(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter([
            path("ws/painel/<int:sessao_id>/", PainelConsumer.as_asgi()),
        ]))
    ),
})
