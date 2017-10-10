from datetime import datetime as dt

from django.core.mail import EmailMultiAlternatives, get_connection, send_mail
from django.core.urlresolvers import reverse
from django.template import Context, loader
from django.utils import timezone

from sapl.base.models import CasaLegislativa
from sapl.settings import EMAIL_SEND_USER

from .models import AcompanhamentoMateria


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


def criar_email_confirmacao(base_url, casa_legislativa, materia, hash_txt=''):

    if not casa_legislativa:
        raise ValueError("Casa Legislativa é obrigatória")

    if not materia:
        raise ValueError("Matéria é obrigatória")

    # FIXME i18n
    casa_nome = (casa_legislativa.nome + ' de ' +
                 casa_legislativa.municipio + '-' +
                 casa_legislativa.uf)

    materia_url = reverse('sapl.materia:materialegislativa_detail',
                          kwargs={'pk': materia.id})
    confirmacao_url = reverse('sapl.materia:acompanhar_confirmar',
                              kwargs={'pk': materia.id})

    autores = []
    for autoria in materia.autoria_set.all():
        autores.append(autoria.autor.nome)

    templates = load_email_templates(['email/acompanhar.txt',
                                      'email/acompanhar.html'],
                                     {"casa_legislativa": casa_nome,
                                      "logotipo": casa_legislativa.logotipo,
                                      "descricao_materia": materia.ementa,
                                      "autoria": autores,
                                      "hash_txt": hash_txt,
                                      "base_url": base_url,
                                      "materia": str(materia),
                                      "materia_url": materia_url,
                                      "confirmacao_url": confirmacao_url, })
    return templates


def do_envia_email_confirmacao(base_url, casa, materia, destinatario):
    #
    # Envia email de confirmacao para atualizações de tramitação
    #

    sender = EMAIL_SEND_USER
    # FIXME i18n
    subject = "[SAPL] " + str(materia) + " - Ative o Acompanhamento da Materia"
    messages = []
    recipients = []

    email_texts = criar_email_confirmacao(base_url,
                                          casa,
                                          materia,
                                          destinatario.hash,)
    recipients.append(destinatario.email)
    messages.append({
        'recipient': destinatario.email,
        'subject': subject,
        'txt_message': email_texts[0],
        'html_message': email_texts[1]
    })

    enviar_emails(sender, recipients, messages)


def criar_email_tramitacao(base_url, casa_legislativa, materia, status,
                           unidade_destino, hash_txt=''):

    if not casa_legislativa:
        raise ValueError("Casa Legislativa é obrigatória")

    if not materia:
        raise ValueError("Matéria é obrigatória")

    # FIXME i18n
    casa_nome = (casa_legislativa.nome + ' de ' +
                 casa_legislativa.municipio + '-' +
                 casa_legislativa.uf)

    url_materia = reverse('sapl.materia:tramitacao_list',
                          kwargs={'pk': materia.id})
    url_excluir = reverse('sapl.materia:acompanhar_excluir',
                          kwargs={'pk': materia.id})

    autores = []
    for autoria in materia.autoria_set.all():
        autores.append(autoria.autor.nome)

    tramitacao = materia.tramitacao_set.last()

    templates = load_email_templates(['email/tramitacao.txt',
                                      'email/tramitacao.html'],
                                     {"casa_legislativa": casa_nome,
                                      "data_registro": dt.strftime(
                                          timezone.now(),
                                          "%d/%m/%Y"),
                                      "cod_materia": materia.id,
                                      "logotipo": casa_legislativa.logotipo,
                                      "descricao_materia": materia.ementa,
                                      "autoria": autores,
                                      "data": tramitacao.data_tramitacao,
                                      "status": status,
                                      "localizacao": unidade_destino,
                                      "texto_acao": tramitacao.texto,
                                      "hash_txt": hash_txt,
                                      "materia": str(materia),
                                      "base_url": base_url,
                                      "materia_url": url_materia,
                                      "excluir_url": url_excluir})
    return templates


def do_envia_email_tramitacao(base_url, materia, status, unidade_destino):
    #
    # Envia email de tramitacao para usuarios cadastrados
    #
    destinatarios = AcompanhamentoMateria.objects.filter(materia=materia,
                                                         confirmado=True)
    casa = CasaLegislativa.objects.first()

    sender = EMAIL_SEND_USER
    # FIXME i18n
    subject = "[SAPL] " + str(materia) + \
              " - Acompanhamento de Materia Legislativa"

    connection = get_connection()
    connection.open()

    for destinatario in destinatarios:
        try:
            email_texts = criar_email_tramitacao(base_url,
                                                 casa,
                                                 materia,
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
                'Erro ao enviar e-mail de acompanhamento de matéria.')

    connection.close()
