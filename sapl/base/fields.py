import hashlib
import posixpath
from pathlib import Path
from uuid import uuid4

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

    def __str__(self):
        """Return the original filename for display (not the UUID storage path)."""
        if not self:
            return ''
        meta_attr = f'{self.field.name}_metadata'
        meta = getattr(self.instance, meta_attr, None)
        if meta and meta.original_filename:
            return meta.original_filename
        # Fallback: basename of storage path (may be UUID for newly uploaded files
        # whose metadata row hasn't been committed yet).
        return Path(self.name).name if self.name else ''

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

    def generate_filename(self, instance, filename):
        """
        Override: substitute a UUID for the filename in the upload_to path so
        that newly uploaded files get stable, unguessable storage paths like
        sapl/public/normajuridica/2025/9395/<uuid>.pdf  (RFC §6.3).

        For replacement uploads (Case 2) the existing meta UUID is reused so
        the physical path — and therefore /documentos/<uuid>/ — stays stable.
        For first uploads (Case 1) a fresh UUID is generated and stashed on the
        instance under _pending_uuid_<fieldname> for pre_save to pick up when
        creating the FileMetadata row.
        """
        # 1. Let upload_to produce the directory + original filename.
        if callable(self.upload_to):
            upload_name = self.upload_to(instance, filename)
        else:
            upload_name = posixpath.join(self.upload_to, filename)

        # 2. Determine the UUID to embed in the path.
        meta_attr = f'{self.name}_metadata'
        meta = getattr(instance, meta_attr, None)
        if meta is not None:
            # Replacement (Case 2): reuse existing UUID — path stays identical,
            # OverwriteStorage replaces the bytes in-place.
            file_uuid = str(meta.uuid)
        else:
            # First upload (Case 1): generate a fresh UUID and stash it so
            # pre_save can wire it into the new FileMetadata row.
            file_uuid = str(uuid4())
            setattr(instance, f'_pending_uuid_{self.name}', file_uuid)

        # 3. Replace the filename portion with <uuid><ext>.
        ext = Path(filename).suffix.lower()
        directory = posixpath.dirname(upload_name)
        new_name = posixpath.join(directory, f'{file_uuid}{ext}') if directory else f'{file_uuid}{ext}'

        return self.storage.generate_filename(new_name)

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
        # file_before.name is set to the original upload name by FileDescriptor.__get__
        # when it wraps the UploadedFile — more reliable than file_before.file.name
        # which for TemporaryUploadedFile is the NamedTemporaryFile path.
        if has_new_upload:
            original_filename = Path(file_before.name).name if file_before.name else ''
        else:
            original_filename = ''

        file = super().pre_save(instance, add)
        # file.name is now the UUID-based storage path from generate_filename,
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
                # Use the UUID that generate_filename already baked into the path
                # so that FileMetadata.uuid matches the on-disk filename.
                pending_uuid = getattr(instance, f'_pending_uuid_{self.name}', None)
                meta_kwargs = dict(
                    storage_name=storage_name,
                    original_filename=original_filename,
                    file_size_bytes=size,
                    content_hash=digest,
                )
                if pending_uuid:
                    from uuid import UUID
                    meta_kwargs['uuid'] = UUID(pending_uuid)
                    # Clean up the temporary stash attribute.
                    try:
                        delattr(instance, f'_pending_uuid_{self.name}')
                    except AttributeError:
                        pass
                meta = FileMetadata(**meta_kwargs)
                meta.save()
                setattr(instance, f'{meta_attr}_id', meta.pk)
            else:
                # Case 2: replacement — reuse the existing row so the stable uuid
                # (and /documentos/<uuid>/) never changes.
                # For UUID-based paths the old and new paths are identical
                # (same uuid, same ext) — OverwriteStorage already replaced the
                # bytes in-place, so we must NOT delete the newly written file.
                if meta_before.storage_name != storage_name:
                    # Legacy (non-UUID) paths: old path differs → delete old file.
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
