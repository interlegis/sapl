from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from sapl.materia.models import Tramitacao
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


@receiver(post_delete, sender=Tramitacao)
def status_tramitacao_materia(sender, instance, **kwargs):
    if instance.turno == 'F':
        materia = instance.materia
        materia.em_tramitacao = True
        materia.save()
