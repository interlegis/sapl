from datetime import datetime as dt

from django.core.mail import EmailMultiAlternatives, get_connection, send_mail
from django.core.urlresolvers import reverse
from django.template import Context, loader
from django.utils import timezone

from sapl.base.models import CasaLegislativa
from sapl.settings import EMAIL_SEND_USER

from .models import AcompanhamentoDocumento


def load_email_templates(templates, context={}):

    emails = []
    for t in templates:
        tpl = loader.get_template(t)
        email = tpl.render(Context(context))
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


def criar_email_confirmacao(base_url, casa_legislativa, documento, hash_txt=''):

    if not casa_legislativa:
        raise ValueError("Casa Legislativa é obrigatória")

    if not documento:
        raise ValueError("Documento é obrigatório")

    # FIXME i18n
    casa_nome = (casa_legislativa.nome + ' de ' +
                 casa_legislativa.municipio + '-' +
                 casa_legislativa.uf)

    documento_url = reverse('sapl.protocoloadm:documentoadministrativo_detail',
                          kwargs={'pk': documento.id})
    confirmacao_url = reverse('sapl.protocoloadm:acompanhar_confirmar',
                              kwargs={'pk': documento.id})


    templates = load_email_templates(['email/acompanhar.txt',
                                      'email/acompanhar.html'],
                                     {"casa_legislativa": casa_nome,
                                      "logotipo": casa_legislativa.logotipo,
                                      "descricao_documento": documento.assunto,
                                      "hash_txt": hash_txt,
                                      "base_url": base_url,
                                      "documento": str(documento),
                                      "documento_url": documento_url,
                                      "confirmacao_url": confirmacao_url, })
    return templates


def do_envia_email_confirmacao(base_url, casa, documento, destinatario):
    #
    # Envia email de confirmacao para atualizações de tramitação
    #

    sender = EMAIL_SEND_USER
    # FIXME i18n
    subject = "[SAPL] " + str(documento) + " - Ative o Acompanhamento do Documento"
    messages = []
    recipients = []

    email_texts = criar_email_confirmacao(base_url,
                                          casa,
                                          documento,
                                          destinatario.hash,)
    recipients.append(destinatario.email)
    messages.append({
        'recipient': destinatario.email,
        'subject': subject,
        'txt_message': email_texts[0],
        'html_message': email_texts[1]
    })

    enviar_emails(sender, recipients, messages)


def criar_email_tramitacao(base_url, casa_legislativa, documento, status,
                           unidade_destino, hash_txt=''):

    if not casa_legislativa:
        raise ValueError("Casa Legislativa é obrigatória")

    if not documento:
        raise ValueError("Documento é obrigatória")

    # FIXME i18n
    casa_nome = (casa_legislativa.nome + ' de ' +
                 casa_legislativa.municipio + '-' +
                 casa_legislativa.uf)

    url_documento = reverse('sapl.documento:tramitacao_list',
                          kwargs={'pk': documento.id})
    url_excluir = reverse('sapl.documento:acompanhar_excluir',
                          kwargs={'pk': documento.id})

    tramitacao = documento.tramitacao_set.last()

    templates = load_email_templates(['email/tramitacao.txt',
                                      'email/tramitacao.html'],
                                     {"casa_legislativa": casa_nome,
                                      "data_registro": dt.strftime(
                                          timezone.now(),
                                          "%d/%m/%Y"),
                                      "cod_documento": documento.id,
                                      "logotipo": casa_legislativa.logotipo,
                                      "descricao_documento": documento.assunto,
                                      "data": tramitacao.data_tramitacao,
                                      "status": status,
                                      "localizacao": unidade_destino,
                                      "texto_acao": tramitacao.texto,
                                      "hash_txt": hash_txt,
                                      "documento": str(documento),
                                      "base_url": base_url,
                                      "documento_url": url_documento,
                                      "excluir_url": url_excluir})
    return templates


def do_envia_email_tramitacao(base_url, documento, status, unidade_destino):
    #
    # Envia email de tramitacao para usuarios cadastrados
    #
    destinatarios = AcompanhamentoDocumento.objects.filter(documento=documento,
                                                         confirmado=True)
    casa = CasaLegislativa.objects.first()

    sender = EMAIL_SEND_USER
    # FIXME i18n
    subject = "[SAPL] " + str(documento) + \
              " - Acompanhamento de Documento Administrativo"

    connection = get_connection()
    connection.open()

    for destinatario in destinatarios:
        try:
            email_texts = criar_email_tramitacao(base_url,
                                                 casa,
                                                 documento,
                                                 status,
                                                 unidade_destino,
                                                 destinatario.hash,)

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
                'Erro ao enviar e-mail de acompanhamento de documento.')

    connection.close()
