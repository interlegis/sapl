from django.core.management.base import BaseCommand

from sapl.legacy.migration import recria_constraints


class Command(BaseCommand):

    help = (u'Recria constraints do PostgreSQL excluidas durante '
            'migração de dados')

    def handle(self, *args, **options):
        recria_constraints()
