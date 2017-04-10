from subprocess import PIPE, call
from threading import Thread

from django.db.models.signals import post_delete, post_save

from sapl.settings import PROJECT_DIR

from .models import DocumentoAcessorio, MateriaLegislativa


class UpdateIndexCommand(Thread):
    def run(self):
        call([PROJECT_DIR.child('manage.py'), 'update_index'],
             stdout=PIPE)


def save_texto(sender, instance, **kwargs):
    update_index = UpdateIndexCommand()
    update_index.start()


def delete_texto(sender, instance, **kwargs):
    update_index = UpdateIndexCommand()
    update_index.start()


post_save.connect(save_texto, sender=MateriaLegislativa)
post_save.connect(save_texto, sender=DocumentoAcessorio)
post_delete.connect(delete_texto, sender=MateriaLegislativa)
post_delete.connect(delete_texto, sender=DocumentoAcessorio)
