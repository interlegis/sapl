from django.core.management.base import BaseCommand

from sapl.legacy.migracao import migrar


class Command(BaseCommand):

    help = 'Migração de dados do SAPL 2.5 para o SAPL 3.1'

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            action='store_true',
            default=False,
            dest='apagar_do_legado',
            help='Apagar entradas migradas do legado',
        )

    def handle(self, *args, **options):
        migrar(apagar_do_legado=options['apagar_do_legado'])
