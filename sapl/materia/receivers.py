from django.dispatch import receiver

from sapl.materia.signals import tramitacao_signal
from sapl.utils import get_base_url

from .email_utils import do_envia_email_tramitacao


@receiver(tramitacao_signal)
def handle_tramitacao_signal(sender, **kwargs):
    tramitacao = kwargs.get("post")
    request = kwargs.get("request")
    materia = tramitacao.materia

    do_envia_email_tramitacao(
        get_base_url(request),
        materia,
        tramitacao.status,
        tramitacao.unidade_tramitacao_destino)
