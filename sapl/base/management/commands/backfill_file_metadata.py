"""
Backfill FileMetadata rows for all existing uploaded files.

Run once after deploying MetadataFileField to production.  Safe to interrupt
and re-run: idempotent in both phases.

Phase 1 — creates missing FileMetadata rows for parent-model instances whose
           _metadata FK is NULL (files uploaded before MetadataFileField was deployed).
Phase 2 — fills in content_hash / file_size_bytes for FileMetadata rows that
           exist but are missing those lazy fields (RFC §8 query:
           WHERE content_hash = '' OR file_size_bytes IS NULL).

By default both phases run.  Use --phase1 or --phase2 to run only one.

Usage:
    python manage.py backfill_file_metadata                      # both phases
    python manage.py backfill_file_metadata --phase1             # create missing rows only
    python manage.py backfill_file_metadata --phase2             # fill size/hash only
    python manage.py backfill_file_metadata --phase1 --rate-limit=20
    python manage.py backfill_file_metadata --phase1 --app materia --model materialegislativa
    python manage.py backfill_file_metadata --phase2 --skip-hash
    python manage.py backfill_file_metadata --dry-run
"""
import hashlib
import os
import time
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
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
        'Idempotent — Phase 1 creates missing rows, Phase 2 fills in '
        'content_hash / file_size_bytes for incomplete rows (RFC §8).'
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
            help='Restrict Phase 1 to a single app_label.',
        )
        parser.add_argument(
            '--model', type=str, default=None,
            help='Restrict Phase 1 to a single model_name (requires --app).',
        )
        parser.add_argument(
            '--skip-hash', action='store_true',
            help='Skip content_hash computation (only stat for file_size_bytes).',
        )
        parser.add_argument(
            '--phase1', action='store_true',
            help='Run Phase 1 only (create missing FileMetadata rows).',
        )
        parser.add_argument(
            '--phase2', action='store_true',
            help='Run Phase 2 only (fill in content_hash / file_size_bytes for incomplete rows).',
        )

    def handle(self, *args, **options):
        from sapl.base.models import FileMetadata

        batch_size = options['batch_size']
        rate_limit = options['rate_limit']
        dry_run = options['dry_run']
        only_app = options['app']
        only_model = options['model']
        skip_hash = options['skip_hash']
        run_phase1 = options['phase1']
        run_phase2 = options['phase2']
        # if neither flag given, run both
        if not run_phase1 and not run_phase2:
            run_phase1 = run_phase2 = True
        start_time = time.time()

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be written.'))

        total_created = 0
        total_updated = 0
        total_errors = 0

        # ── Phase 1: create FileMetadata rows for FK-NULL parent instances ────────

        if run_phase1:
            self.stdout.write('Phase 1: creating missing FileMetadata rows...')

            targets = [
                (app, model, field)
                for (app, model, field) in METADATA_FILE_FIELDS
                if (only_app is None or app == only_app)
                and (only_model is None or model == only_model)
            ]

            for app_label, model_name, field_name in targets:
                try:
                    Model = apps.get_model(app_label, model_name)
                except LookupError:
                    self.stdout.write(
                        self.style.ERROR(f'  Model {app_label}.{model_name} not found — skipping.'))
                    continue

                meta_fk = f'{field_name}_metadata'
                qs = Model.objects.filter(
                    **{f'{field_name}__isnull': False,
                       f'{meta_fk}__isnull': True}
                ).exclude(
                    **{field_name: ''}
                ).only('pk', field_name, meta_fk)

                count = qs.count()
                if count == 0:
                    self.stdout.write(
                        f'  {app_label}.{model_name}.{field_name}: up to date.')
                    continue

                self.stdout.write(
                    f'  {app_label}.{model_name}.{field_name}: {count} rows to backfill...')

                batch_start = time.time()
                processed = 0

                for instance in qs.iterator(chunk_size=batch_size):
                    field_file = getattr(instance, field_name)
                    storage_name = field_file.name
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
                                f'    pk={instance.pk}: cannot read {full_path}: {e}'))
                        total_errors += 1

                    if dry_run:
                        self.stdout.write(
                            f'    [dry-run] pk={instance.pk} → {storage_name}')
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
                            app_label=app_label,
                            model_name=model_name,
                            field_name=field_name,
                            owner_pk=instance.pk,
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
                    self.style.SUCCESS(f'    done: {processed} rows created.'))
        else:
            self.stdout.write('Phase 1: skipped.')

        # ── Phase 2: fill in content_hash / file_size_bytes for incomplete rows ──
        # RFC §8: query WHERE content_hash = '' OR file_size_bytes IS NULL.
        # --app/--model do not restrict Phase 2 (it operates on FileMetadata directly).

        if run_phase2:
            self.stdout.write('Phase 2: filling in missing size/hash for existing rows...')

            incomplete_qs = FileMetadata.objects.filter(
                Q(content_hash='') | Q(file_size_bytes__isnull=True)
            )
            count = incomplete_qs.count()

            if count == 0:
                self.stdout.write('  all rows already have size and hash.')
            else:
                self.stdout.write(f'  {count} rows to update...')

                batch_start = time.time()
                processed = 0

                for meta in incomplete_qs.iterator(chunk_size=batch_size):
                    full_path = os.path.join(settings.MEDIA_ROOT, meta.storage_name)

                    try:
                        stat = os.stat(full_path)
                        file_size_bytes = stat.st_size
                        content_hash = (
                            _compute_hash(full_path)
                            if not skip_hash and not meta.content_hash
                            else meta.content_hash
                        )
                    except OSError as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  uuid={meta.uuid}: cannot read {full_path}: {e}'))
                        total_errors += 1
                        continue

                    if dry_run:
                        self.stdout.write(
                            f'  [dry-run] uuid={meta.uuid} → size={file_size_bytes}')
                        total_updated += 1
                        processed += 1
                        continue

                    update_fields = ['backfilled_at']
                    if meta.file_size_bytes is None:
                        meta.file_size_bytes = file_size_bytes
                        update_fields.append('file_size_bytes')
                    if not meta.content_hash and not skip_hash:
                        meta.content_hash = content_hash
                        update_fields.append('content_hash')
                    meta.backfilled_at = timezone.now()
                    meta.save(update_fields=update_fields)

                    total_updated += 1
                    processed += 1

                    if rate_limit > 0:
                        elapsed = time.time() - batch_start
                        target_elapsed = processed / rate_limit
                        if target_elapsed > elapsed:
                            time.sleep(target_elapsed - elapsed)

                self.stdout.write(
                    self.style.SUCCESS(f'  done: {processed} rows updated.'))
        else:
            self.stdout.write('Phase 2: skipped.')

        elapsed = time.time() - start_time
        self.stdout.write('')
        self.stdout.write(
            f'Backfill complete — created: {total_created}, updated: {total_updated}, '
            f'errors (file missing): {total_errors}, elapsed: {elapsed:.1f}s'
        )
        if dry_run:
            self.stdout.write(self.style.WARNING('(dry run — nothing was written)'))
