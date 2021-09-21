import os

import django
from channels.http import AsgiHandler
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import sapl.painel.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sapl.settings')
django.setup()

application = ProtocolTypeRouter({
  "http": AsgiHandler(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
            sapl.painel.routing.websocket_urlpatterns
        )
  ),
})