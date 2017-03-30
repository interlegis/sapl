from django.core.management.base import BaseCommand

from sapl.legacy.migracao_documentos import migrar_documentos


class Command(BaseCommand):

    help = u'Migração documentos do SAPL 2.5 para o SAPL 3.1'

    def handle(self, *args, **options):
        migrar_documentos()
