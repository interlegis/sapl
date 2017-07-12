from django.db.models.signals import post_delete, post_save

import django.dispatch

from sapl.utils import delete_texto, save_texto

from .models import DocumentoAcessorio, MateriaLegislativa


tramitacao_signal = django.dispatch.Signal(providing_args=['post', 'request'])
