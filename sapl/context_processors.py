import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from sapl.utils import google_recaptcha_configured as google_recaptcha_configured_utils, sapn_is_enabled
from sapl.utils import mail_service_configured as mail_service_configured_utils


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
        logger.warning(_('Servidor de email não configurado.'))
        return {'mail_service_configured': False}
    return {'mail_service_configured': True}


def google_recaptcha_configured(request):

    if not google_recaptcha_configured_utils():
        logger = logging.getLogger(__name__)
        logger.warning(_('Google Recaptcha não configurado.'))
        return {'google_recaptcha_configured': False}
    return {'google_recaptcha_configured': True}


def enable_sapn(request):
    return {
        'sapl_as_sapn': sapn_is_enabled(),
        'nome_sistema': _('Sistema de Apoio ao Processo Legislativo')
        if not sapn_is_enabled()
        else _('Sistema de Apoio à Publicação de Leis e Normas')
    }
