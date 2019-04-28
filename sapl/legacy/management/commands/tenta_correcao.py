from django.core.management.base import BaseCommand

from sapl.legacy.migracao import tenta_correcao


class Command(BaseCommand):
    def handle(self, *args, **options):
        tenta_correcao()
