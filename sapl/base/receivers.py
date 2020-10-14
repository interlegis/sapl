import inspect
import logging

from django.conf import settings
from django.core import serializers
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from sapl.base.email_utils import do_envia_email_tramitacao
from sapl.base.models import AuditLog
from sapl.base.signals import tramitacao_signal
from sapl.materia.models import Tramitacao
from sapl.protocoloadm.models import TramitacaoAdministrativo
from sapl.utils import get_base_url


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

    do_envia_email_tramitacao(
        get_base_url(request),
        tipo,
        doc_mat,
        tramitacao.status,
        tramitacao.unidade_tramitacao_destino)


@receiver(post_delete)
def status_tramitacao_materia(sender, instance, **kwargs):
    if sender == Tramitacao:
        if instance.status.indicador == 'F':
            materia = instance.materia
            materia.em_tramitacao = True
            materia.save()
    elif sender == TramitacaoAdministrativo:
        if instance.status.indicador == 'F':
            documento = instance.documento
            documento.tramitacao = True
            documento.save()


def audit_log_function(sender, **kwargs):
    if not sender or \
            hasattr(sender, '_meta') and not sender._meta or \
            hasattr(sender._meta, 'app_config') and not sender._meta.app_config or \
            not sender._meta.app_config.name.startswith('sapl'):
        return

    logger = logging.getLogger(__name__)

    u = None
    for i in inspect.stack():
        r = i.frame.f_locals.get('request', None)
        try:
            if r and \
                    r.user._meta.label == settings.AUTH_USER_MODEL:
                u = r.user
                break
        except:
            pass

    try:
        instance = kwargs.get('instance')
        operation = kwargs.get('operation')
        user = u
        model_name = instance.__class__.__name__
        app_name = instance._meta.app_label
        object_id = instance.id
        data = serializers.serialize('json', [instance])

        if len(data) > AuditLog.MAX_DATA_LENGTH:
            data = data[:AuditLog.MAX_DATA_LENGTH]

        if user:
            username = user.username
        else:
            username = ''

        AuditLog.objects.create(username=username,
                                operation=operation,
                                model_name=model_name,
                                app_name=app_name,
                                timestamp=timezone.now(),
                                object_id=object_id,
                                object=data)
    except Exception as e:
        logger.error('Error saving auditing log object')
        logger.error(e)


@receiver(post_delete)
def audit_log_post_delete(sender, **kwargs):
    audit_log_function(sender, operation='D', **kwargs)


@receiver(post_save)
def audit_log_post_save(sender, **kwargs):
    operation = 'C' if kwargs.get('created') else 'U'
    audit_log_function(sender, operation=operation, **kwargs)
