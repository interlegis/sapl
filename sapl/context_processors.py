import logging

from django.utils.translation import ugettext_lazy as _

from sapl.utils import cached_call, get_base_url
from sapl.utils import google_recaptcha_configured as google_recaptcha_configured_utils
from sapl.utils import mail_service_configured as mail_service_configured_utils
from sapl.utils import sapn_is_enabled


def parliament_info(request):
    from sapl.base.views import get_casalegislativa

    casa = get_casalegislativa()
    if casa:
        return casa.__dict__
    else:
        return {}


def mail_service_configured(request):
    if not mail_service_configured_utils(request):
        logger = logging.getLogger(__name__)
        logger.warning(_("Servidor de email não configurado."))
        return {"mail_service_configured": False}
    return {"mail_service_configured": True}


def google_recaptcha_configured(request):
    if not google_recaptcha_configured_utils():
        logger = logging.getLogger(__name__)
        logger.warning(_("Google Recaptcha não configurado."))
        return {"google_recaptcha_configured": False}
    return {"google_recaptcha_configured": True}


@cached_call("site-title", timeout=60 * 2)
def enable_sapn(request):
    verbose_name = (
        _("Sistema de Apoio ao Processo Legislativo")
        if not sapn_is_enabled()
        else _("Sistema de Apoio à Publicação de Leis e Normas")
    )

    from sapl.base.models import CasaLegislativa

    casa_legislativa = CasaLegislativa.objects.first()
    nome_casa = (
        casa_legislativa.nome if casa_legislativa and casa_legislativa.nome else ""
    )

    return {
        "sapl_as_sapn": sapn_is_enabled(),
        "nome_sistema": verbose_name,
        "nome_casa": nome_casa,
        "base_url": get_base_url(request),
    }
