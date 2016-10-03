from django.core.management.base import BaseCommand

from sapl.legacy import migration


class Command(BaseCommand):
    help = u'Faz a migração de dados do SAPL 2.5 para o SAPL 3.1'

    def handle(self, *args, **options):
        migration.migrate()
