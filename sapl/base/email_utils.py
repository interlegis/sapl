from datetime import datetime as dt
import logging

from django.core.mail import EmailMultiAlternatives, get_connection, send_mail
from django.core.urlresolvers import reverse
from django.template import Context, loader
from django.utils import timezone

from sapl.base.models import CasaLegislativa
from sapl.materia.models import AcompanhamentoMateria
from sapl.protocoloadm.models import AcompanhamentoDocumento
from sapl.settings import EMAIL_SEND_USER
from sapl.utils import mail_service_configured

from django.utils.translation import ugettext_lazy as _

def load_email_templates(templates, context={}):

    emails = []
    for t in templates:
        tpl = loader.get_template(t)
        email = tpl.render(context)
        if t.endswith(".html"):
            email = email.replace('\n', '').replace('\r', '')
        emails.append(email)
    return emails


def enviar_emails(sender, recipients, messages):
    '''
        Recipients is a string list of email addresses

        Messages is an array of dicts of the form:
        {'recipient': 'address', # useless????
         'subject': 'subject text',
         'txt_message': 'text message',
         'html_message': 'html message'
        }
    '''

    if len(messages) == 1:
        # sends an email simultaneously to all recipients
        send_mail(messages[0]['subject'],
                  messages[0]['txt_message'],
                  sender,
                  recipients,
                  html_message=messages[0]['html_message'],
                  fail_silently=False)

    elif len(recipients) > len(messages):
        raise ValueError("Message list should have size 1 \
                         or equal recipient list size. \
                         recipients: %s, messages: %s" % (recipients, messages)
                         )

    else:
        # sends an email simultaneously to all reciepients
        for (d, m) in zip(recipients, messages):
            send_mail(m['subject'],
                      m['txt_message'],
                      sender,
                      [d],
                      html_message=m['html_message'],
                      fail_silently=False)


def criar_email_confirmacao(base_url, casa_legislativa, doc_mat, tipo, hash_txt=''):

    if not casa_legislativa:
        raise ValueError("Casa Legislativa é obrigatória")

    if not doc_mat:
        if tipo == "materia":
            msg = "Matéria é obrigatória"
        else:
            msg = "Documento é obrigatório"
        raise ValueError(msg)

    # FIXME i18n
    casa_nome = ("{} de {} - {}".format(casa_legislativa.nome,
                                        casa_legislativa.municipio,
                                        casa_legislativa.uf))

    if tipo == "materia":
        doc_mat_url = reverse('sapl.materia:materialegislativa_detail',
                              kwargs={'pk': doc_mat.id})
        confirmacao_url = reverse('sapl.materia:acompanhar_confirmar',
                                  kwargs={'pk': doc_mat.id})
        ementa = doc_mat.ementa
        autores = [autoria.autor.nome for autoria in doc_mat.autoria_set.all()]
    else:
        doc_mat_url = reverse('sapl.protocoloadm:documentoadministrativo_detail',
                              kwargs={'pk': doc_mat.id})
        confirmacao_url = reverse('sapl.protocoloadm:acompanhar_confirmar',
                                  kwargs={'pk': doc_mat.id})
        ementa = doc_mat.assunto
        autores = ""

    templates = load_email_templates(['email/acompanhar.txt',
                                      'email/acompanhar.html'],
                                     {"casa_legislativa": casa_nome,
                                      "logotipo": casa_legislativa.logotipo,
                                      "descricao_materia": ementa,
                                      "autoria": autores,
                                      "hash_txt": hash_txt,
                                      "base_url": base_url,
                                      "materia": str(doc_mat),
                                      "materia_url": doc_mat_url,
                                      "confirmacao_url": confirmacao_url, })
    return templates


def do_envia_email_confirmacao(base_url, casa, tipo, doc_mat, destinatario):
    #
    # Envia email de confirmacao para atualizações de tramitação
    #

    logger = logging.getLogger(__name__)

    if not mail_service_configured():
        logger.warning(_('Servidor de email não configurado.'))
        return

    sender = EMAIL_SEND_USER
    # FIXME i18n
    if tipo == "materia":
        msg = " - Ative o Acompanhamento da Matéria"
    else:
        msg = " - Ative o Acompanhamento de Documento"
    subject = "[SAPL] {} {}".format(str(doc_mat), msg)
    messages = []
    recipients = []

    email_texts = criar_email_confirmacao(base_url,
                                          casa,
                                          doc_mat,
                                          tipo,
                                          destinatario.hash,)
    recipients.append(destinatario.email)
    messages.append({
        'recipient': destinatario.email,
        'subject': subject,
        'txt_message': email_texts[0],
        'html_message': email_texts[1]
    })

    enviar_emails(sender, recipients, messages)


def criar_email_tramitacao(base_url, casa_legislativa, tipo, doc_mat, status,
                           unidade_destino, hash_txt=''):

    if not casa_legislativa:
        raise ValueError("Casa Legislativa é obrigatória")

    if not doc_mat:
        if tipo == "materia":
            msg = "Matéria é obrigatória"
        else:
            msg = "Documento é obrigatório"
        raise ValueError(msg)

    # FIXME i18n
    casa_nome = ("{} de {} - {}".format(casa_legislativa.nome,
                                        casa_legislativa.municipio,
                                        casa_legislativa.uf))
    if tipo == "materia":
        doc_mat_url = reverse('sapl.materia:tramitacao_list',
                              kwargs={'pk': doc_mat.id})
        url_excluir = reverse('sapl.materia:acompanhar_excluir',
                              kwargs={'pk': doc_mat.id})

        ementa = doc_mat.ementa
        autores = [autoria.autor.nome for autoria in doc_mat.autoria_set.all()]
        tramitacao = doc_mat.tramitacao_set.last()

    else:
        doc_mat_url = reverse('sapl.protocoloadm:tramitacaoadministrativo_list',
                              kwargs={'pk': doc_mat.id})
        url_excluir = reverse('sapl.protocoloadm:acompanhar_excluir',
                              kwargs={'pk': doc_mat.id})
        autores = ""
        ementa = doc_mat.assunto
        tramitacao = doc_mat.tramitacaoadministrativo_set.last()

    templates = load_email_templates(['email/tramitacao.txt',
                                      'email/tramitacao.html'],
                                     {"casa_legislativa": casa_nome,
                                      "data_registro": dt.strftime(
                                          timezone.now(),
                                          "%d/%m/%Y"),
                                      "cod_materia": doc_mat.id,
                                      "logotipo": casa_legislativa.logotipo,
                                      "descricao_materia": ementa,
                                      "autoria": autores,
                                      "data": tramitacao.data_tramitacao,
                                      "status": status,
                                      "localizacao": unidade_destino,
                                      "texto_acao": tramitacao.texto,
                                      "hash_txt": hash_txt,
                                      "materia": str(doc_mat),
                                      "base_url": base_url,
                                      "materia_url": doc_mat_url,
                                      "excluir_url": url_excluir})
    return templates


def do_envia_email_tramitacao(base_url, tipo, doc_mat, status, unidade_destino):
    #
    # Envia email de tramitacao para usuarios cadastrados
    #

    logger = logging.getLogger(__name__)
    if not mail_service_configured():
        logger.warning(_('Servidor de email não configurado.'))
        return

    if tipo == "materia":
        destinatarios = AcompanhamentoMateria.objects.filter(materia=doc_mat,
                                                             confirmado=True)
    else:
        destinatarios = AcompanhamentoDocumento.objects.filter(documento=doc_mat,
                                                               confirmado=True)

    if not destinatarios:
        logger.debug(_('Não existem destinatários cadastrados para essa matéria.'))
        return

    casa = CasaLegislativa.objects.first()

    sender = EMAIL_SEND_USER
    # FIXME i18nn
    if tipo == "materia":
        msg = " - Acompanhamento de Matéria Legislativa"
    else:
        msg = " - Acompanhamento de Documento"
    subject = "[SAPL] {} {}".format(str(doc_mat), msg)

    connection = get_connection()
    connection.open()

    for destinatario in destinatarios:
        try:
            email_texts = criar_email_tramitacao(base_url,
                                                 casa,
                                                 tipo,
                                                 doc_mat,
                                                 status,
                                                 unidade_destino,
                                                 destinatario.hash)

            email = EmailMultiAlternatives(
                subject,
                email_texts[0],
                sender,
                [destinatario.email],
                connection=connection)
            email.attach_alternative(email_texts[1], "text/html")
            email.send()

        # Garantia de que, mesmo com o lançamento de qualquer exceção,
        # a conexão será fechada
        except Exception:
            connection.close()
            raise Exception(
                'Erro ao enviar e-mail de acompanhamento de matéria.')


    connection.close()
