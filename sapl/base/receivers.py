from django.db.models.signals import post_delete
from django.dispatch import receiver

from sapl.base.signals import tramitacao_signal
from sapl.protocoloadm.models import TramitacaoAdministrativo
from sapl.utils import get_base_url

from .tasks import task_envia_email_tramitacao


@receiver(tramitacao_signal)
def handle_tramitacao_signal(sender, **kwargs):
    tramitacao = kwargs.get("post")
    request = kwargs.get("request")
    if 'protocoloadm' in str(sender):
        doc_mat = tramitacao.documento
        tipo = "documento"
    elif 'materia' in str(sender):
        tipo = "materia"
        doc_mat = tramitacao.materia

    kwargs = {'base_url': get_base_url(request), 'tipo': tipo, 'doc_mat_id': doc_mat.id,
              'tramitacao_status_id': tramitacao.status.id,
              'tramitacao_unidade_tramitacao_destino_id': tramitacao.unidade_tramitacao_destino.id}

    task_envia_email_tramitacao.delay(kwargs)


@receiver(post_delete)
def status_tramitacao_materia(sender, instance, **kwargs):
    if isinstance(sender, TramitacaoAdministrativo):
        if instance.status.indicador == 'F':
            materia = instance.materia
            materia.em_tramitacao = True
            materia.save()
    elif isinstance(sender, TramitacaoAdministrativo):
        if instance.status.indicador == 'F':
            documento = instance.documento
            documento.tramitacao = True
            documento.save()
