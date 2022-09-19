import inspect
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db.models.signals import post_delete, post_save, \
    post_migrate
from django.db.utils import DEFAULT_DB_ALIAS
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sapl.base.email_utils import do_envia_email_tramitacao
from sapl.base.models import AuditLog, TipoAutor, Autor
from sapl.decorators import receiver_multi_senders
from sapl.materia.models import Tramitacao
from sapl.protocoloadm.models import TramitacaoAdministrativo
from sapl.utils import get_base_url, models_with_gr_for_model

models_with_gr_for_autor = models_with_gr_for_model(Autor)


@receiver_multi_senders(post_save, senders=models_with_gr_for_autor)
def handle_update_autor_related(sender, **kwargs):
    # for m in models_with_gr_for_autor:
    instance = kwargs.get('instance')
    autor = instance.autor.first()
    if autor:
        autor.nome = str(instance)
        autor.save()


@receiver(post_save, sender=Tramitacao)
@receiver(post_save, sender=TramitacaoAdministrativo)
def handle_tramitacao_signal(sender, **kwargs):
    logger = logging.getLogger(__name__)

    tramitacao = kwargs.get('instance')

    if isinstance(tramitacao, Tramitacao):
        tipo = "materia"
        doc_mat = tramitacao.materia
    else:
        tipo = "documento"
        doc_mat = tramitacao.documento

    pilha_de_execucao = inspect.stack()
    for i in pilha_de_execucao:
        if i.function == 'migrate':
            return
        request = i.frame.f_locals.get('request', None)
        if request:
            break

    if not request:
        logger.warning("Email não enviado, objeto request é None.")
        return
    try:
        do_envia_email_tramitacao(
            get_base_url(request),
            tipo,
            doc_mat,
            tramitacao.status,
            tramitacao.unidade_tramitacao_destino)
    except Exception as e:
        logger.error(f'user={request.user.username}. Tramitação criada, mas e-mail de acompanhamento '
                     'de matéria não enviado. Há problemas na configuração '
                     'do e-mail. ' + str(e))


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
    try:
        if not (sender._meta.app_config.name.startswith('sapl') or
                sender._meta.label == settings.AUTH_USER_MODEL):
            return
    except:
        # não é necessário usar logger, aqui é usada apenas para
        # eliminar um o if complexo
        return

    instance = kwargs.get('instance')
    if instance._meta.model == AuditLog:
        return

    logger = logging.getLogger(__name__)

    u = None
    pilha_de_execucao = inspect.stack()
    for i in pilha_de_execucao:
        if i.function == 'migrate':
            return
        r = i.frame.f_locals.get('request', None)
        try:
            if r.user._meta.label == settings.AUTH_USER_MODEL:
                u = r.user
                break
        except:
            # não é necessário usar logger, aqui é usada apenas para
            # eliminar um o if complexo
            pass

    try:
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


def cria_models_tipo_autor(app_config=None, verbosity=2, interactive=True,
                           using=DEFAULT_DB_ALIAS, **kwargs):

    print("\n\033[93m\033[1m{}\033[0m".format(
        _('Atualizando registros TipoAutor do SAPL:')))
    for model in models_with_gr_for_autor:
        content_type = ContentType.objects.get_for_model(model)
        tipo_autor = TipoAutor.objects.filter(
            content_type=content_type.id).exists()

        if tipo_autor:
            msg1 = "Carga de {} não efetuada.".format(
                TipoAutor._meta.verbose_name)
            msg2 = " Já Existe um {} {} relacionado...".format(
                TipoAutor._meta.verbose_name,
                model._meta.verbose_name)
            msg = "  {}{}".format(msg1, msg2)
        else:
            novo_autor = TipoAutor()
            novo_autor.content_type_id = content_type.id
            novo_autor.descricao = model._meta.verbose_name
            novo_autor.save()
            msg1 = "Carga de {} efetuada.".format(
                TipoAutor._meta.verbose_name)
            msg2 = " {} {} criado...".format(
                TipoAutor._meta.verbose_name, content_type.model)
            msg = "  {}{}".format(msg1, msg2)
        print(msg)
    # Disconecta função para evitar a chamada repetidas vezes.
    post_migrate.disconnect(receiver=cria_models_tipo_autor)


post_migrate.connect(receiver=cria_models_tipo_autor)
