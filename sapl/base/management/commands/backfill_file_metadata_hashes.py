"""
Phase 2 backfill — fills file_size_bytes and content_hash for FileMetadata rows
where backfilled_at IS NULL. I/O-bound; designed to run at low priority over
days or weeks without affecting production traffic.

Safe to interrupt and resume: sets backfilled_at on each completed row.

Usage:
    python manage.py backfill_file_metadata_hashes [--batch-size=200] [--rate-limit=20]

Progress query:
    SELECT
        COUNT(*) FILTER (WHERE backfilled_at IS NULL)     AS pending,
        COUNT(*) FILTER (WHERE backfilled_at IS NOT NULL) AS done
    FROM base_file_metadata;
"""
import hashlib
import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


def _compute_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


class Command(BaseCommand):
    help = (
        'Phase 2 backfill: fill file_size_bytes and content_hash for FileMetadata rows '
        'where backfilled_at IS NULL. Resumable and rate-limited.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size', type=int, default=200,
            help='Rows per iteration (default: 200).',
        )
        parser.add_argument(
            '--rate-limit', type=int, default=0,
            help='Max rows per second (0 = unlimited).',
        )
        parser.add_argument(
            '--skip-hash', action='store_true',
            help='Only populate file_size_bytes, skip SHA-256 (faster).',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report counts without writing.',
        )

    def handle(self, *args, **options):
        from sapl.base.models import FileMetadata

        batch_size = options['batch_size']
        rate_limit = options['rate_limit']
        skip_hash = options['skip_hash']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — nothing will be written.'))

        qs = FileMetadata.objects.filter(backfilled_at__isnull=True)
        total = qs.count()
        self.stdout.write(f'Phase 2: {total} rows to process...')

        processed = 0
        errors = 0
        batch_start = time.time()

        for meta in qs.iterator(chunk_size=batch_size):
            full_path = os.path.join(settings.MEDIA_ROOT, meta.storage_name)
            try:
                stat = os.stat(full_path)
                file_size_bytes = stat.st_size
                content_hash = _compute_hash(full_path) if not skip_hash else ''
            except OSError as e:
                self.stdout.write(self.style.WARNING(
                    f'  uuid={meta.uuid}: cannot read {full_path}: {e}'))
                errors += 1
                continue

            if not dry_run:
                update_fields = ['backfilled_at']
                meta.backfilled_at = timezone.now()
                if meta.file_size_bytes is None:
                    meta.file_size_bytes = file_size_bytes
                    update_fields.append('file_size_bytes')
                if not meta.content_hash and not skip_hash:
                    meta.content_hash = content_hash
                    update_fields.append('content_hash')
                meta.save(update_fields=update_fields)

            processed += 1

            if rate_limit > 0:
                elapsed = time.time() - batch_start
                target = processed / rate_limit
                if target > elapsed:
                    time.sleep(target - elapsed)

        self.stdout.write(self.style.SUCCESS(
            f'Phase 2 complete — processed: {processed}, errors: {errors}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('(dry run — nothing was written)'))
