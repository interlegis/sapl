"""Seed the public watermark from verifiable historical evidence."""
import json

from django.core import serializers
from django.core.management.base import BaseCommand
from django.core.serializers.base import DeserializationError
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from sapl.base.atualizacao import (content_models, public_values, record,
                                   visibility)
from sapl.base.models import AuditLog


class Command(BaseCommand):
    help = ('Inicializa a atualização pública a partir de evidências '
            'persistidas, sem atribuir a data da execução.')

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Exibe as evidências sem gravar alterações.')
        parser.add_argument('--database', default='default')

    def handle(self, *args, **options):
        using = options['database']
        candidates = {}
        previous = {}
        history = {}
        config_modes = {}
        document_mode = '?'
        skipped = 0
        eligible = {model._meta.label_lower: model
                    for model in content_models()}

        def consider(instance, timestamp, public, session):
            key = 'global' if public else (
                'sessao:%s' % session.pk if session else None)
            if key is None or timestamp is None:
                return
            candidate = (timestamp, instance._meta.label_lower,
                         instance.pk, session if not public else None)
            if key not in candidates or timestamp > candidates[key][0]:
                candidates[key] = candidate

        # auto_now alone is not evidence: AddField migrations can populate it
        # with the deployment date, and private/technical edits also change it.
        # Replay full audit snapshots, comparing only public values and using
        # historical owners rather than their present-day visibility.
        logs = AuditLog.objects.using(using).filter(
            app_name__in={m._meta.app_label for m in eligible.values()}
        ).order_by('timestamp', 'pk')
        for log in logs.iterator():
            label = '%s.%s' % (log.app_name, log.model_name.lower())
            if label == 'base.appconfig':
                old_mode = document_mode
                data = log.data if isinstance(log.data, dict) else {}
                fields = data.get('fields', {})
                fields = fields if isinstance(fields, dict) else {}
                mode = fields.get('documentos_administrativos')
                valid = (data.get('model') == label and
                         data.get('pk') == log.object_id and
                         mode in ('O', 'R'))
                if log.operation == 'D':
                    config_modes.pop(log.object_id, None)
                else:
                    config_modes[log.object_id] = mode if valid else '?'
                document_mode = (config_modes[max(config_modes)]
                                 if config_modes else '?')
                if (old_mode in ('O', 'R') and
                        document_mode in ('O', 'R') and
                        old_mode != document_mode and any(
                            key[0] == 'protocoloadm.documentoadministrativo'
                            and not obj.restrito
                            for key, obj in history.items())):
                    if ('global' not in candidates or
                            log.timestamp > candidates['global'][0]):
                        candidates['global'] = (
                            log.timestamp, label, log.object_id, None)
                continue
            if label not in eligible or log.operation not in ('C', 'U', 'D'):
                continue
            try:
                data = log.data
                if not isinstance(data, dict) or data.get('model') != label:
                    skipped += 1
                    continue
                fields = data.get('fields', {})
                if not isinstance(fields, dict) or any(
                        f.name not in fields
                        for f in eligible[label]._meta.concrete_fields
                        if not f.primary_key):
                    skipped += 1
                    continue
                # Dates and files are converted by Django, exactly as with
                # fixture loading, but the deserialized object is never saved.
                obj = next(serializers.deserialize(
                    'json', json.dumps([data]), using=using)).object
                if str(obj.pk) != str(log.object_id):
                    skipped += 1
                    continue
                public, session = visibility(
                    obj, at=log.timestamp, history=history,
                    document_mode=document_mode)
                values = public_values(obj)
                key = (label, obj.pk)
                before = previous.get(key)
                # A lone U entry cannot prove that a public field changed.
                proven = log.operation in ('C', 'D') or (
                    before is not None and before[0] != values)
                was_public = before is not None and before[1]
                if proven:
                    consider(obj, log.timestamp, public or was_public, session)
                if log.operation == 'D':
                    previous.pop(key, None)
                    history.pop(key, None)
                else:
                    previous[key] = (values, public)
                    history[key] = obj
            except (DeserializationError, ObjectDoesNotExist, ValueError,
                    TypeError, KeyError, StopIteration):
                skipped += 1

        # Scheduled evidence must still belong to a currently hidden session.
        from sapl.sessao.models import SessaoPlenaria
        with transaction.atomic(using=using):
            for key, candidate in sorted(candidates.items()):
                timestamp, origin, pk, session = candidate
                if session is not None:
                    session = SessaoPlenaria.objects.using(using).filter(
                        pk=session.pk).first()
                    if session is None:
                        continue
                    public, unused = visibility(session)
                    if public:
                        session = None
                self.stdout.write('%s: %s (%s #%s)' % (
                    key, timestamp.isoformat(), origin, pk))
                if not options['dry_run']:
                    record(timestamp, origin, pk, using, session=session)
        self.stdout.write(
            '%s evidência(s); %s registro(s) sem comprovação.' % (
                len(candidates), skipped))
