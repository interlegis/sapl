import logging

from django.shortcuts import redirect
from django.urls import reverse


class CheckWeakPasswordMiddleware:
    logger = logging.getLogger(__name__)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and request.session.get("weak_password", False)
            and request.path != reverse("sapl.base:alterar_senha")
            and request.path != reverse("sapl.base:logout")
        ):
            logging.warning(f"Usuário {request.user.username} possui senha fraca.")
            return redirect("sapl.base:alterar_senha")

        return self.get_response(request)
