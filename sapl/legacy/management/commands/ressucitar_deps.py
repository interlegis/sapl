from django.core.management.base import BaseCommand

from sapl.legacy.scripts.ressucita_dependencias import adiciona_ressucitar


class Command(BaseCommand):

    help = 'Ressucita dependências apagadas ' \
        'que são necessárias para migrar outros registros'

    def handle(self, *args, **options):
        adiciona_ressucitar()
