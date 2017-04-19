from django.db.models.signals import post_delete, post_save
from sapl.utils import save_texto, delete_texto

from .models import DocumentoAcessorio, MateriaLegislativa


post_save.connect(save_texto, sender=MateriaLegislativa)
post_save.connect(save_texto, sender=DocumentoAcessorio)
post_delete.connect(delete_texto, sender=MateriaLegislativa)
post_delete.connect(delete_texto, sender=DocumentoAcessorio)
