import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from sapl.base.views import get_casalegislativa
from sapl.utils import mail_service_configured as mail_service_configured_utils


def parliament_info(request):
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
