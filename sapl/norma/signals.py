from django.db.models.signals import post_delete, post_save

from sapl.utils import delete_texto, save_texto

from .models import NormaJuridica
