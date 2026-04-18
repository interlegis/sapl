"""
Backfill FileMetadata rows for all existing uploaded files.

Run once after deploying MetadataFileField to production.  Safe to interrupt
and re-run: processes only rows where the _metadata FK is NULL and the file
field is non-empty.

Usage:
    python manage.py backfill_file_metadata
    python manage.py backfill_file_metadata --batch-size=200 --rate-limit=20
    python manage.py backfill_file_metadata --dry-run
    python manage.py backfill_file_metadata --app materia --model materialegislativa
"""
import hashlib
import os
import time
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# Every (app_label, model_name, field_name) that uses MetadataFileField.
# Kept in sync with SERVE_FILE_FIELDS in sapl/base/views.py.
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


def _compute_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


class Command(BaseCommand):
    help = (
        'Backfill FileMetadata rows for all existing uploaded files. '
        'Idempotent — skips rows that already have a _metadata FK set.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size', type=int, default=500,
            help='Number of rows to process per batch (default: 500).',
        )
        parser.add_argument(
            '--rate-limit', type=int, default=0,
            help='Max rows per second (0 = unlimited; useful on NFS to avoid I/O storms).',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what would be done without writing anything.',
        )
        parser.add_argument(
            '--app', type=str, default=None,
            help='Restrict to a single app_label.',
        )
        parser.add_argument(
            '--model', type=str, default=None,
            help='Restrict to a single model_name (requires --app).',
        )
        parser.add_argument(
            '--skip-hash', action='store_true',
            help='Skip content_hash computation (only stat for file_size_bytes).',
        )

    def handle(self, *args, **options):
        from sapl.base.models import FileMetadata

        batch_size = options['batch_size']
        rate_limit = options['rate_limit']
        dry_run = options['dry_run']
        only_app = options['app']
        only_model = options['model']
        skip_hash = options['skip_hash']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be written.'))

        targets = [
            (app, model, field)
            for (app, model, field) in METADATA_FILE_FIELDS
            if (only_app is None or app == only_app)
            and (only_model is None or model == only_model)
        ]

        total_created = 0
        total_skipped = 0
        total_errors = 0

        for app_label, model_name, field_name in targets:
            try:
                Model = apps.get_model(app_label, model_name)
            except LookupError:
                self.stdout.write(
                    self.style.ERROR(f'Model {app_label}.{model_name} not found — skipping.'))
                continue

            meta_fk = f'{field_name}_metadata'
            # Only process rows where file is set but metadata FK is NULL.
            qs = Model.objects.filter(
                **{f'{field_name}__isnull': False,
                   f'{meta_fk}__isnull': True}
            ).exclude(
                **{field_name: ''}
            ).only('pk', field_name, meta_fk)

            count = qs.count()
            if count == 0:
                self.stdout.write(
                    f'{app_label}.{model_name}.{field_name}: already up to date.')
                continue

            self.stdout.write(
                f'{app_label}.{model_name}.{field_name}: {count} rows to backfill...')

            batch_start = time.time()
            processed = 0

            for instance in qs.iterator(chunk_size=batch_size):
                field_file = getattr(instance, field_name)
                storage_name = field_file.name  # relative path stored in DB
                original_filename = Path(storage_name).name

                full_path = os.path.join(settings.MEDIA_ROOT, storage_name)

                file_size_bytes = None
                content_hash = ''

                try:
                    stat = os.stat(full_path)
                    file_size_bytes = stat.st_size
                    if not skip_hash:
                        content_hash = _compute_hash(full_path)
                except OSError as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  pk={instance.pk}: cannot read {full_path}: {e}'))
                    total_errors += 1

                if dry_run:
                    self.stdout.write(
                        f'  [dry-run] pk={instance.pk} → {storage_name}')
                    total_created += 1
                    processed += 1
                    continue

                with transaction.atomic():
                    meta = FileMetadata(
                        storage_name=storage_name,
                        original_filename=original_filename,
                        file_size_bytes=file_size_bytes,
                        content_hash=content_hash,
                        backfilled_at=timezone.now(),
                    )
                    meta.save()
                    setattr(instance, f'{meta_fk}_id', meta.pk)
                    instance.save(update_fields=[f'{meta_fk}_id'])

                total_created += 1
                processed += 1

                if rate_limit > 0:
                    elapsed = time.time() - batch_start
                    target_elapsed = processed / rate_limit
                    if target_elapsed > elapsed:
                        time.sleep(target_elapsed - elapsed)

            self.stdout.write(
                self.style.SUCCESS(
                    f'  done: {processed} rows processed.'))

        self.stdout.write('')
        self.stdout.write(
            f'Backfill complete — created: {total_created}, '
            f'errors (file missing): {total_errors}.')
        if dry_run:
            self.stdout.write(self.style.WARNING('(dry run — nothing was written)'))
