# sapl/asgi.py
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sapl.settings")

import django
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.http import AsgiHandler  # Django 2.2 uses AsgiHandler, not django.core.asgi
from django.urls import path

from sapl.painel.consumers import PainelConsumer, HealthConsumer

application = ProtocolTypeRouter({
    "http": AsgiHandler(),
    "websocket": AuthMiddlewareStack(URLRouter([
        # path("ws/painel/", PainelConsumer.as_asgi()),
        path("ws/painel/<int:controller_id>/", PainelConsumer.as_asgi()),
    ])),
})
