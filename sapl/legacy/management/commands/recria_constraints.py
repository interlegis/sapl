from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = (u'Recria constraints do PostgreSQL excluidas durante '
            'migração de dados')

    def handle(self, *args, **options):
        pass
