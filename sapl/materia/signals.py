from django.db.models.signals import post_delete, post_save

import django.dispatch

from sapl.utils import delete_texto, save_texto

from .models import DocumentoAcessorio, MateriaLegislativa, Tramitacao


tramitacao_signal = django.dispatch.Signal(providing_args=["post", "request"])

# post_save.connect(save_texto, sender=MateriaLegislativa)
# post_save.connect(save_texto, sender=DocumentoAcessorio)
# post_delete.connect(delete_texto, sender=MateriaLegislativa)
# post_delete.connect(delete_texto, sender=DocumentoAcessorio)
