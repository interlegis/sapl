from datetime import datetime

from django.core.mail import send_mass_mail
from django.core.urlresolvers import reverse
from django.dispatch import receiver

from sapl.base.models import CasaLegislativa
from sapl.materia.signals import tramitacao_signal
from sapl.settings import EMAIL_SEND_USER
from sapl.utils import get_base_url

from .models import AcompanhamentoMateria
from .email_utils import load_email_templates


@receiver(tramitacao_signal)
def handle_tramitacao_signal(sender, **kwargs):
    tramitacao = kwargs.get("post")
    request = kwargs.get("request")
    materia = tramitacao.materia

    destinatarios = AcompanhamentoMateria.objects.filter(
        materia=materia,
        confirmado=True)

    casa = CasaLegislativa.objects.first()

    if not casa:
        raise ValueError('Casa Legislativa é obrigatória')

    # FIXME i18n
    casa_nome = (casa.nome + ' de ' +
                 casa.municipio + '-' +
                 casa.uf)

    sender = EMAIL_SEND_USER

    # FIXME i18n
    subject = "[SAPL] " + str(materia) + \
              " - Acompanhamento de Materia Legislativa"

    base_url = get_base_url(request)
    url_materia = reverse('sapl.materia:tramitacao_list',
                          kwargs={'pk': materia.id})
    url_excluir = reverse('sapl.materia:acompanhar_excluir',
                          kwargs={'pk': materia.id})

    autores = []
    for autoria in materia.autoria_set.all():
        autores.append(autoria.autor.nome)

    templates = load_email_templates(
        ['email/tramitacao.txt',
         'email/tramitacao.html'],
        {"casa_legislativa": casa_nome,
         "data_registro": datetime.now().strftime(
             "%d/%m/%Y"),
         "cod_materia": materia.id,
         "logotipo": casa.logotipo,
         "descricao_materia": materia.ementa,
         "autoria": autores,
         "data": tramitacao.data_tramitacao,
         "status": tramitacao.status,
         "localizacao": tramitacao.unidade_tramitacao_destino,
         "texto_acao": tramitacao.texto,
         "hash_txt": '',
         "materia": str(materia),
         "base_url": base_url,
         "materia_url": url_materia,
         "excluir_url": url_excluir})

    lista_emails = destinatarios.values_list('email', flat=True).distinct()

    send_mass_mail(
        ((subject, templates[0], sender, lista_emails),),
        fail_silently=True)
