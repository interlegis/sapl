from django.core import management
from django.core.management.base import BaseCommand

from sapl.legacy.migracao import migrar, migrar_dados


class Command(BaseCommand):

    help = 'Migração de dados do SAPL 2.5 para o SAPL 3.1'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            dest='force',
            help='Não interativa: pula confirmação de exclusão dos dados',
        )
        parser.add_argument(
            '--dados',
            action='store_true',
            default=False,
            dest='dados',
            help='migra somente dados',
        )

    def handle(self, *args, **options):
        management.call_command('migrate')
        somente_dados, interativo = options['dados'], not options['force']
        if somente_dados:
            migrar_dados(interativo=interativo)
        else:
            migrar(interativo=interativo)
