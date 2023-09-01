from django.http import HttpResponseForbidden
import logging

# lista de IPs permitidos (localhost, redes locais, etc)
# https://en.wikipedia.org/wiki/Reserved_IP_addresses
ALLOWED_IPS = [
    '127.0.0.1',
    '::1',
    '10.0.0.0/8',
    '172.16.0.0/12',
    '192.168.0.0/16',
    'fc00::/7',
    '::1',
    'fe80::/10',
    '192.0.2.0/24',
    '2001:db8::/32',
    '224.0.0.0/4',
    'ff00::/8'
]

RESTRICTED_ENDPOINTS = ['/metrics']


class EndpointRestrictionMiddleware:
    logging.getLogger(__name__)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # IP do cliente
        client_ip = request.META.get('REMOTE_ADDR')

        # bloqueia acesso a endpoints restritos para IPs nao permitidos
        if request.path in RESTRICTED_ENDPOINTS and client_ip not in ALLOWED_IPS:
            return HttpResponseForbidden('Acesso proibido')

        return self.get_response(request)
