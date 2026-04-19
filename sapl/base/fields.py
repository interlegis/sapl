import hashlib
import logging
import posixpath
import unicodedata
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import magic
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import models, transaction
from django.db.models.fields.files import FieldFile
from django.db.models.signals import post_save

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MetadataFieldFile — FieldFile subclass with semantic URL support
# ---------------------------------------------------------------------------

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
        return Path(self.name).name if self.name else ''

    @property
    def url(self):
        if not self:
            raise ValueError("The '%s' attribute has no file associated with it." % self.field.name)

        instance = self.instance
        meta_attr = f'{self.field.name}_metadata'
        meta = getattr(instance, meta_attr, None)

        if meta is None:
            return self.storage.url(self.name)

        pk = getattr(instance, 'pk', None)

        if pk is not None:
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

        return f'/documentos/{meta.uuid}/'


# ---------------------------------------------------------------------------
# Filename sanitization
# ---------------------------------------------------------------------------

def _sanitize_filename(name: str) -> str:
    name = name.strip()
    name = ''.join(c for c in name if ord(c) >= 0x20 and ord(c) != 0x7F)
    name = unicodedata.normalize('NFC', name)
    name = ' '.join(name.split())
    name = name[:255]
    if not name:
        name = 'untitled'
    return name


# ---------------------------------------------------------------------------
# MIME validation
# ---------------------------------------------------------------------------

FIELD_ALLOWED_TYPES = {
    ('materia', 'materialegislativa', 'texto_original'): frozenset([
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/rtf', 'text/plain',
    ]),
    ('materia', 'documentoacessorio', 'arquivo'): frozenset([
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg', 'image/png', 'image/tiff',
    ]),
    ('materia', 'proposicao', 'texto_original'): frozenset([
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]),
    ('protocoloadm', 'documentoadministrativo', 'texto_integral'): frozenset([
        'application/pdf',
    ]),
    ('protocoloadm', 'documentoacessorioadministrativo', 'arquivo'): frozenset([
        'application/pdf', 'image/jpeg', 'image/png', 'image/tiff',
    ]),
    ('norma', 'normajuridica', 'texto_integral'): frozenset([
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]),
    ('norma', 'anexonormajuridica', 'anexo_arquivo'): frozenset([
        'application/pdf', 'image/jpeg', 'image/png',
    ]),
    **{
        (app, model, field): frozenset(['application/pdf', 'image/jpeg', 'image/png', 'image/tiff'])
        for app, model, field in [
            ('sessao', 'sessaoplenaria', 'upload_pauta'),
            ('sessao', 'sessaoplenaria', 'upload_ata'),
            ('sessao', 'sessaoplenaria', 'upload_anexo'),
            ('sessao', 'justificativaausencia', 'upload_anexo'),
            ('comissoes', 'reuniao', 'upload_pauta'),
            ('comissoes', 'reuniao', 'upload_ata'),
            ('comissoes', 'reuniao', 'upload_anexo'),
            ('comissoes', 'documentoacessorio', 'arquivo'),
            ('audiencia', 'audienciapublica', 'upload_pauta'),
            ('audiencia', 'audienciapublica', 'upload_ata'),
            ('audiencia', 'audienciapublica', 'upload_anexo'),
            ('audiencia', 'anexoaudienciapublica', 'arquivo'),
        ]
    },
}

_MIME_TO_EXTENSIONS = {
    'application/pdf': {'.pdf'},
    'application/msword': {'.doc'},
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {'.docx'},
    'application/rtf': {'.rtf'},
    'text/plain': {'.txt'},
    'image/jpeg': {'.jpg', '.jpeg'},
    'image/png': {'.png'},
    'image/tiff': {'.tif', '.tiff'},
}


def _validate_file_type(file_obj, app_label, model_name, field_name):
    allowed = FIELD_ALLOWED_TYPES.get((app_label, model_name, field_name))
    if allowed is None:
        return
    header = file_obj.file.read(512)
    file_obj.file.seek(0)
    sniffed = magic.from_buffer(header, mime=True)
    if sniffed not in allowed:
        raise ValidationError(
            f'Tipo de arquivo não permitido: {sniffed}. '
            f'Permitidos: {", ".join(sorted(allowed))}'
        )
    ext = Path(file_obj.name).suffix.lower()
    if ext and sniffed in _MIME_TO_EXTENSIONS:
        if ext not in _MIME_TO_EXTENSIONS[sniffed]:
            raise ValidationError(
                f'Extensão {ext!r} não corresponde ao tipo detectado ({sniffed}).'
            )


# ---------------------------------------------------------------------------
# Content hash + size
# ---------------------------------------------------------------------------

def _compute_size_and_hash(field_file) -> tuple:
    h = hashlib.sha256()
    size = 0
    with field_file.open('rb') as fh:
        for chunk in iter(lambda: fh.read(65536), b''):
            h.update(chunk)
            size += len(chunk)
    return size, h.hexdigest()


# ---------------------------------------------------------------------------
# Blob deletion
# ---------------------------------------------------------------------------

def _delete_blob_safe(storage_name: str) -> None:
    try:
        default_storage.delete(storage_name)
    except Exception:
        logger.warning('Failed to delete blob %s', storage_name, exc_info=True)


# ---------------------------------------------------------------------------
# Content-Disposition
# ---------------------------------------------------------------------------

_INLINE_EXTENSIONS = frozenset(['.pdf'])


def _content_disposition(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    disposition = 'inline' if ext in _INLINE_EXTENSIONS else 'attachment'
    safe_ascii = filename.encode('ascii', 'replace').decode()
    encoded = quote(filename, safe='')
    return f'{disposition}; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded}'


# ---------------------------------------------------------------------------
# Visibility / cache helpers
# ---------------------------------------------------------------------------

_PRIVATE_FIELDS = frozenset({
    ('materia', 'proposicao', 'texto_original'),
    ('protocoloadm', 'documentoadministrativo', 'texto_integral'),
    ('protocoloadm', 'documentoacessorioadministrativo', 'arquivo'),
})


def _visibility(meta) -> str:
    return 'private' if (meta.app_label, meta.model_name, meta.field_name) in _PRIVATE_FIELDS else 'public'


def _is_public(meta) -> bool:
    return (meta.app_label, meta.model_name, meta.field_name) not in _PRIVATE_FIELDS


# ---------------------------------------------------------------------------
# MetadataFileField
# ---------------------------------------------------------------------------

class MetadataFileField(models.FileField):
    """
    Drop-in replacement for models.FileField.

    Injects a companion FK '<fieldname>_metadata' → FileMetadata and maintains
    it across upload, replacement, and clear operations.
    """

    attr_class = MetadataFieldFile

    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        fk = models.ForeignKey(
            'base.FileMetadata',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+',
            verbose_name='File metadata',
        )
        cls.add_to_class(f'{name}_metadata', fk)
        post_save.connect(self._fix_owner_pk, sender=cls, weak=False)

    def _fix_owner_pk(self, sender, instance, created, **kwargs):
        """Fills owner_pk after INSERT — pk is None at pre_save time for new objects."""
        if not created:
            return
        meta = getattr(instance, f'{self.attname}_metadata', None)
        if meta is not None and meta.owner_pk is None:
            meta.owner_pk = instance.pk
            meta.save(update_fields=['owner_pk'])

    def generate_filename(self, instance, filename):
        """
        Substitutes a UUID for the filename in the upload_to path so newly
        uploaded files get stable, unguessable storage paths (RFC §6.3).
        """
        if callable(self.upload_to):
            upload_name = self.upload_to(instance, filename)
        else:
            upload_name = posixpath.join(self.upload_to, filename)

        meta_attr = f'{self.name}_metadata'
        meta = getattr(instance, meta_attr, None)
        if meta is not None:
            file_uuid = str(meta.uuid)
        else:
            file_uuid = str(uuid4())
            setattr(instance, f'_pending_uuid_{self.name}', file_uuid)

        ext = Path(filename).suffix.lower()
        directory = posixpath.dirname(upload_name)
        new_name = posixpath.join(directory, f'{file_uuid}{ext}') if directory else f'{file_uuid}{ext}'

        return self.storage.generate_filename(new_name)

    def pre_save(self, instance, add):
        from sapl.base.models import FileMetadata

        meta_attr = f'{self.attname}_metadata'
        file_before = getattr(instance, self.attname)
        meta_before = getattr(instance, meta_attr, None)

        has_new_upload = bool(file_before) and not getattr(file_before, '_committed', True)
        is_clearing = not file_before and meta_before is not None

        # Sanitize original filename before storage renames it.
        # file_before.name holds the user-supplied name at this point.
        if has_new_upload:
            original_filename = _sanitize_filename(Path(file_before.name).name) if file_before.name else 'untitled'
        else:
            original_filename = ''

        if has_new_upload:
            _validate_file_type(file_before, instance._meta.app_label,
                                instance._meta.model_name, self.attname)

        file = super().pre_save(instance, add)

        if is_clearing:
            old_storage_name = meta_before.storage_name
            setattr(instance, f'{meta_attr}_id', None)
            meta_before.delete()
            transaction.on_commit(lambda: _delete_blob_safe(old_storage_name))

        elif file and has_new_upload:
            storage_name = file.name
            size, digest = _compute_size_and_hash(file)

            if meta_before is None:
                # Case 1: first upload.
                pending_uuid = getattr(instance, f'_pending_uuid_{self.name}', None)
                meta_kwargs = dict(
                    storage_name=storage_name,
                    original_filename=original_filename,
                    file_size_bytes=size,
                    content_hash=digest,
                    app_label=instance._meta.app_label,
                    model_name=instance._meta.model_name,
                    field_name=self.attname,
                    owner_pk=instance.pk or None,
                )
                if pending_uuid:
                    from uuid import UUID
                    meta_kwargs['uuid'] = UUID(pending_uuid)
                    try:
                        delattr(instance, f'_pending_uuid_{self.name}')
                    except AttributeError:
                        pass
                with transaction.atomic():
                    meta = FileMetadata(**meta_kwargs)
                    meta.save()
                    setattr(instance, f'{meta_attr}_id', meta.pk)
            else:
                # Case 2: replacement — reuse existing row so uuid (and /documentos/<uuid>/) never changes.
                with transaction.atomic():
                    locked = FileMetadata.objects.select_for_update().get(pk=meta_before.pk)
                    old_storage_name = locked.storage_name
                    locked.version += 1
                    locked.storage_name = storage_name
                    locked.original_filename = original_filename
                    locked.file_size_bytes = size
                    locked.content_hash = digest
                    locked.app_label = instance._meta.app_label
                    locked.model_name = instance._meta.model_name
                    locked.field_name = self.attname
                    locked.owner_pk = instance.pk
                    locked.save(update_fields=[
                        'version', 'storage_name', 'original_filename',
                        'file_size_bytes', 'content_hash',
                        'app_label', 'model_name', 'field_name', 'owner_pk',
                    ])
                if old_storage_name != storage_name:
                    transaction.on_commit(lambda: _delete_blob_safe(old_storage_name))

        return file
