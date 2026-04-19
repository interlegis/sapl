"""
Phase 1 backfill — creates FileMetadata rows for parent-model instances whose
_metadata FK is NULL. Pure DB work, no disk I/O. Completes in seconds.

Safe to re-run (idempotent). Safe to run from multiple workers simultaneously
(bulk_create with ignore_conflicts=True handles races).

Usage:
    python manage.py backfill_file_metadata_structural [--batch-size=1000]
"""
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction

METADATA_FILE_FIELDS = [
    ('materia',       'materialegislativa',               'texto_original'),
    ('materia',       'documentoacessorio',               'arquivo'),
    ('materia',       'proposicao',                       'texto_original'),
    ('protocoloadm',  'documentoadministrativo',          'texto_integral'),
    ('protocoloadm',  'documentoacessorioadministrativo', 'arquivo'),
    ('norma',         'normajuridica',                    'texto_integral'),
    ('norma',         'anexonormajuridica',               'anexo_arquivo'),
    ('comissoes',     'reuniao',                          'upload_pauta'),
    ('comissoes',     'reuniao',                          'upload_ata'),
    ('comissoes',     'reuniao',                          'upload_anexo'),
    ('comissoes',     'documentoacessorio',               'arquivo'),
    ('audiencia',     'audienciapublica',                 'upload_pauta'),
    ('audiencia',     'audienciapublica',                 'upload_ata'),
    ('audiencia',     'audienciapublica',                 'upload_anexo'),
    ('audiencia',     'anexoaudienciapublica',            'arquivo'),
    ('sessao',        'sessaoplenaria',                   'upload_pauta'),
    ('sessao',        'sessaoplenaria',                   'upload_ata'),
    ('sessao',        'sessaoplenaria',                   'upload_anexo'),
    ('sessao',        'justificativaausencia',            'upload_anexo'),
    ('sessao',        'orador',                           'upload_anexo'),
    ('sessao',        'oradorexpediente',                 'upload_anexo'),
    ('sessao',        'oradorordemdia',                   'upload_anexo'),
]


class Command(BaseCommand):
    help = (
        'Phase 1 backfill: create FileMetadata rows for existing files (no disk I/O). '
        'Idempotent — skips instances where _metadata FK is already set.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size', type=int, default=1000,
            help='Rows per bulk_create batch (default: 1000).',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report counts without writing.',
        )

    def handle(self, *args, **options):
        from sapl.base.models import FileMetadata

        batch_size = options['batch_size']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — nothing will be written.'))

        total_created = 0

        for app_label, model_name, field_name in METADATA_FILE_FIELDS:
            try:
                Model = apps.get_model(app_label, model_name)
            except LookupError:
                self.stdout.write(self.style.ERROR(
                    f'  {app_label}.{model_name} not found — skipping.'))
                continue

            meta_fk = f'{field_name}_metadata'
            qs = (
                Model.objects
                .filter(**{f'{field_name}__isnull': False, f'{meta_fk}__isnull': True})
                .exclude(**{field_name: ''})
                .only('pk', field_name, meta_fk)
            )
            count = qs.count()
            if count == 0:
                self.stdout.write(f'  {app_label}.{model_name}.{field_name}: up to date.')
                continue

            self.stdout.write(f'  {app_label}.{model_name}.{field_name}: {count} rows...')

            if dry_run:
                total_created += count
                continue

            # Process in batches: bulk_create rows, then bulk_update the FK back.
            batch = []
            instances = []
            for instance in qs.iterator(chunk_size=batch_size):
                field_file = getattr(instance, field_name)
                storage_name = field_file.name
                batch.append(FileMetadata(
                    storage_name=storage_name,
                    original_filename=Path(storage_name).name,
                    app_label=app_label,
                    model_name=model_name,
                    field_name=field_name,
                    owner_pk=instance.pk,
                ))
                instances.append(instance)

                if len(batch) >= batch_size:
                    total_created += self._flush(
                        batch, instances, meta_fk, field_name, Model)
                    batch = []
                    instances = []

            if batch:
                total_created += self._flush(batch, instances, meta_fk, field_name, Model)

            self.stdout.write(self.style.SUCCESS(f'    done.'))

        self.stdout.write(f'Structural backfill complete — created: {total_created}')
        if dry_run:
            self.stdout.write(self.style.WARNING('(dry run — nothing was written)'))

    def _flush(self, batch, instances, meta_fk, field_name, Model):
        from sapl.base.models import FileMetadata

        with transaction.atomic():
            created = FileMetadata.objects.bulk_create(batch, ignore_conflicts=True)

        # Re-query to get PKs for the rows we just inserted (bulk_create may not
        # return PKs on all DB backends, and ignore_conflicts rows have pk=None).
        storage_names = [m.storage_name for m in batch]
        meta_map = {
            m.storage_name: m.pk
            for m in FileMetadata.objects.filter(storage_name__in=storage_names)
        }

        update_instances = []
        for instance in instances:
            field_file = getattr(instance, field_name)
            pk = meta_map.get(field_file.name)
            if pk:
                setattr(instance, f'{meta_fk}_id', pk)
                update_instances.append(instance)

        if update_instances:
            with transaction.atomic():
                Model.objects.bulk_update(update_instances, [f'{meta_fk}_id'])

        return len(created)
