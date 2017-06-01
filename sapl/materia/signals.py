
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from sapl.utils import save_texto, delete_texto

from .models import DocumentoAcessorio, MateriaLegislativa
from .email_utils import do_envia_email_tramitacao


post_save.connect(save_texto, sender=MateriaLegislativa)
post_save.connect(save_texto, sender=DocumentoAcessorio)
post_delete.connect(delete_texto, sender=MateriaLegislativa)
post_delete.connect(delete_texto, sender=DocumentoAcessorio)

#@receiver(post_save, sender=Tramitacao)
#def handle_tramitacao(sender, **kwargs):
#    tramitacao = kwargs.get('instance')
#    do_envia_email_tramitacao(request, materia, status, unidade_destino)
