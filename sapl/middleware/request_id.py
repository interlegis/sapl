import uuid
from sapl.logging.filters import set_request_id

HEADER_NAME = "HTTP_X_REQUEST_ID"
RESPONSE_HEADER = "X-Request-ID"


def _new_id():
    return uuid.uuid4().hex


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # recebe `request_id` do nginx ou do cliente senão cria um
        request_id = request.META.get(HEADER_NAME) or _new_id()
        request_id = str(request_id)[:64]
        request.request_id = request_id
        set_request_id(request_id)
        response = self.get_response(request)
        response[RESPONSE_HEADER] = request_id
        return response
