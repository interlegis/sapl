from django.db.models.signals import post_delete, post_save

from sapl.utils import delete_texto, save_texto

from .models import NormaJuridica

post_save.connect(save_texto, sender=NormaJuridica)
post_delete.connect(delete_texto, sender=NormaJuridica)
