import hashlib
from pathlib import Path

from django.core.files import File
from django.core.files.storage import default_storage
from django.db import models
from django.db.models.fields.files import FieldFile


class MetadataFieldFile(FieldFile):
    """
    FieldFile subclass that returns human-readable URLs via the semantic alias
    pattern /<app>/<model>/<pk>/<field>/download instead of exposing disk paths.

    Falls back to /documentos/<uuid>/ for unsaved instances (pk is None) or
    when the _metadata FK has not been set yet.  The canonical /documentos/<uuid>/
    form is always stable across model/field renames and is what API serializers
    must use (see RFC §10).
    """

    @property
    def url(self):
        if not self:
            raise ValueError("The '%s' attribute has no file associated with it." % self.field.name)

        instance = self.instance
        meta_attr = f'{self.field.name}_metadata'
        meta = getattr(instance, meta_attr, None)

        # Fallback: no metadata row yet (pre-backfill existing file or first save
        # before commit) → return the raw storage URL so nothing breaks.
        if meta is None:
            return self.storage.url(self.name)

        pk = getattr(instance, 'pk', None)

        if pk is not None:
            # Saved instance — return the semantic alias.
            # Lazy import avoids a circular dependency at module load time.
            from django.urls import reverse
            return reverse(
                'serve_model_file',
                kwargs={
                    'app_label': instance._meta.app_label,
                    'model_name': instance._meta.model_name,
                    'pk': pk,
                    'field_name': self.field.name,
                },
            )

        # Unsaved instance — return canonical UUID form.
        return f'/documentos/{meta.uuid}/'


def _compute_size_and_hash(field_file):
    """
    Read the file content once to compute size and SHA-256 digest.
    field_file must be open-able via field_file.open().
    Returns (size_in_bytes, hex_digest).
    """
    h = hashlib.sha256()
    size = 0
    with field_file.open('rb') as fh:
        for chunk in iter(lambda: fh.read(65536), b''):
            h.update(chunk)
            size += len(chunk)
    return size, h.hexdigest()


class MetadataFileField(models.FileField):
    """
    Drop-in replacement for models.FileField.

    Uses MetadataFieldFile as its descriptor so that .url returns the semantic
    alias /<app>/<model>/<pk>/<field>/download for saved instances, and falls
    back to /documentos/<uuid>/ for unsaved instances.

    In addition to normal FileField behaviour, this field:
    1. Injects a companion ForeignKey '<fieldname>_metadata' pointing to
       base.FileMetadata on the owning model class at class-definition time.
    2. In pre_save, creates or updates the FileMetadata row that tracks the
       stable uuid, storage_name, original_filename, size, and hash for the
       uploaded file.

    Four lifecycle scenarios handled in pre_save:
      Case 1 — first upload  : create a new FileMetadata row; set the FK.
      Case 2 — replacement   : delete the old physical file; update the existing
                               FileMetadata row in-place so the uuid (and therefore
                               /documentos/<uuid>/) never changes.
      Case 3 — field cleared : nullify the FK; delete the FileMetadata row;
                               physical file cleanup is deferred to the
                               clean_orphan_files management command.
      Case 4 — no-op re-save : nothing touched.
    """

    attr_class = MetadataFieldFile

    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        # Inject companion FK: e.g. texto_original → texto_original_metadata_id
        fk = models.ForeignKey(
            'base.FileMetadata',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+',
            verbose_name='File metadata',
        )
        cls.add_to_class(f'{name}_metadata', fk)

    def pre_save(self, instance, add):
        from sapl.base.models import FileMetadata

        meta_attr = f'{self.attname}_metadata'
        file_before = getattr(instance, self.attname)
        meta_before = getattr(instance, meta_attr, None)

        # Capture intent BEFORE super() — storage.save() sets _committed=True,
        # erasing the distinction between "new upload" and "already committed".
        has_new_upload = bool(file_before) and not getattr(file_before, '_committed', True)
        is_clearing = not file_before and meta_before is not None

        # Capture browser-supplied filename before storage renames it to the UUID path.
        if has_new_upload and hasattr(file_before, 'file'):
            original_filename = Path(file_before.file.name).name
        else:
            original_filename = ''

        file = super().pre_save(instance, add)
        # file.name is now the full storage path produced by upload_to,
        # e.g. "sapl/public/normajuridica/2025/9395/<uuid>.pdf"

        if is_clearing:
            # Case 3: ClearableFileInput submitted with clear=True.
            # Nullify FK on the in-memory instance immediately so the subsequent
            # model.save() writes NULL — do NOT rely on SET_NULL cascade, which
            # only fires in the DB.  Physical file left for offline cleanup.
            setattr(instance, f'{meta_attr}_id', None)
            meta_before.delete()

        elif file and has_new_upload:
            storage_name = file.name
            size, digest = _compute_size_and_hash(file)

            if meta_before is None:
                # Case 1: first upload — create a new FileMetadata row.
                meta = FileMetadata(
                    storage_name=storage_name,
                    original_filename=original_filename,
                    file_size_bytes=size,
                    content_hash=digest,
                )
                meta.save()
                setattr(instance, f'{meta_attr}_id', meta.pk)
            else:
                # Case 2: replacement — reuse the existing row so the stable uuid
                # (and /documentos/<uuid>/) never changes.  Delete old physical file
                # only after the new one is confirmed saved (super() already returned).
                try:
                    default_storage.delete(meta_before.storage_name)
                except OSError:
                    pass  # already gone — proceed
                meta_before.version += 1
                meta_before.storage_name = storage_name
                meta_before.original_filename = original_filename
                meta_before.file_size_bytes = size
                meta_before.content_hash = digest
                meta_before.save(update_fields=[
                    'version', 'storage_name', 'original_filename',
                    'file_size_bytes', 'content_hash',
                ])

        return file
