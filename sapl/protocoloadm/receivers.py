from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import TramitacaoAdministrativo
from .signals import tramitacao_signal
from sapl.utils import get_base_url

from .email_utils import do_envia_email_tramitacao


@receiver(tramitacao_signal)
def handle_tramitacao_signal(sender, **kwargs):
    tramitacao = kwargs.get("post")
    request = kwargs.get("request")
    documento = tramitacao.documento

    do_envia_email_tramitacao(
        get_base_url(request),
        documento,
        tramitacao.status,
        tramitacao.unidade_tramitacao_destino)


@receiver(post_delete, sender=Tramitacao)
def status_tramitacao_documento(sender, instance, **kwargs):
    if instance.status.indicador == 'F':
        documento = instance.documento
        documento.tramitacao = True
        documento.save()
