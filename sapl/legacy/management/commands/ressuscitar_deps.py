from django.core.management.base import BaseCommand

from sapl.legacy.scripts.ressuscita_dependencias import adiciona_ressuscitar


class Command(BaseCommand):

    help = 'Ressuscita dependências apagadas ' \
        'que são necessárias para migrar outros registros'

    def handle(self, *args, **options):
        adiciona_ressuscitar()
