"""Dates of actual public content changes (issue #3872).

Keep eligibility here, independent of the user performing a write. Bulk
operations must use the helpers below: Django does not emit save signals for
bulk_create, bulk_update or QuerySet.update.
"""
from functools import lru_cache, wraps
from inspect import signature

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import router, transaction
from django.db.models import Q
from django.db.models.fields.files import FileField
from django.db.models.signals import (m2m_changed, post_delete, post_save,
                                      pre_delete, pre_save)
from django.utils import timezone


# An explicit content registry: do not infer eligibility from an app label or
# from API permissions (some technical models also have public endpoints).
CONTENT_MODELS = {
    'base': 'CasaLegislativa Autor',
    'materia': '''MateriaLegislativa TipoMateriaLegislativa AssuntoMateria
        MateriaAssunto Anexada Autoria DespachoInicial DocumentoAcessorio
        Numeracao Tramitacao MateriaEmTramitacao PautaReuniao Relatoria Parecer
        RegimeTramitacao Origem TipoDocumento Orgao TipoFimRelatoria
        StatusTramitacao UnidadeTramitacao''',
    'norma': '''NormaJuridica AssuntoNorma TipoNormaJuridica
        TipoVinculoNormaJuridica NormaRelacionada AnexoNormaJuridica
        AutoriaNorma LegislacaoCitada''',
    'protocoloadm': '''DocumentoAdministrativo DocumentoAcessorioAdministrativo
        TramitacaoAdministrativo Anexado VinculoDocAdminMateria''',
    'sessao': '''SessaoPlenaria SessaoPlenariaPresenca ExpedienteMateria
        OcorrenciaSessao IntegranteMesa ExpedienteSessao Orador
        OradorExpediente OradorOrdemDia OrdemDia PresencaOrdemDia
        RegistroVotacao VotoParlamentar
        JustificativaAusencia RetiradaPauta RegistroLeitura ConsideracoesFinais
        Correspondencia CargoBancada Bancada TipoSessaoPlenaria
        TipoResultadoVotacao TipoExpediente TipoJustificativa
        TipoRetiradaPauta''',
    'comissoes': '''Comissao TipoComissao Periodo CargoComissao Composicao
        Participacao Reuniao DocumentoAcessorio''',
    'parlamentares': '''Legislatura SessaoLegislativa Coligacao
        ComposicaoColigacao Partido Parlamentar Filiacao TipoAfastamento
        Mandato CargoMesa MesaDiretora ComposicaoMesa Frente FrenteCargo
        FrenteParlamentar Bloco BlocoCargo BlocoMembro''',
    'audiencia': 'AudienciaPublica TipoAudienciaPublica AnexoAudienciaPublica',
    'compilacao': '''TextoArticulado Publicacao Dispositivo Vide Nota
        VeiculoPublicacao TipoTextoArticulado TipoDispositivo TipoNota
        TipoVide TipoPublicacao''',
}

# The public parlamentar serializer deliberately omits these fields.
PRIVATE_FIELDS = {
    'parlamentares.parlamentar': frozenset((
        'cpf', 'rg', 'fax',
        'data_nascimento', 'endereco_residencia', 'municipio_residencia',
        'uf_residencia', 'cep_residencia', 'situacao_militar',
        'telefone_residencia', 'titulo_eleitor', 'fax_residencia')),
    'sessao.sessaoplenaria': frozenset(('painel_aberto', 'interativa')),
    'compilacao.textoarticulado': frozenset((
        'editing_locked',
        'editable_only_by_owners')),
}
TECHNICAL_FIELDS = frozenset((
    'id', 'user', 'ip', 'ip_address', 'search',
    'data_ultima_atualizacao', 'ultima_edicao', 'created', 'modified',
    'owner'))

# Follow content owners, never arbitrary foreign keys such as an operator or
# a classification table. The visibility of a child is bounded by its owner.
OWNER_FIELDS = frozenset((
    'sessao_plenaria', 'ordem', 'expediente', 'votacao',
    'documento', 'documento_principal', 'documento_anexado', 'reuniao',
    'audiencia', 'ta', 'dispositivo', 'dispositivo_base', 'dispositivo_ref'))


@lru_cache(maxsize=1)
def content_models():
    return frozenset(
        apps.get_model(app, name)
        for app, names in CONTENT_MODELS.items() for name in names.split())


def public_values(instance):
    excluded = TECHNICAL_FIELDS | PRIVATE_FIELDS.get(
        instance._meta.label_lower, frozenset())
    return {f.attname: getattr(instance, f.attname)
            for f in instance._meta.concrete_fields
            if f.name not in excluded and not f.primary_key
            and not getattr(f, 'auto_now', False)
            and not getattr(f, 'auto_now_add', False)}


def visibility(instance, seen=None, at=None, history=None, document_mode=None):
    """Return (public, scheduled_session) using anonymous access rules."""
    from django.contrib.auth.models import AnonymousUser
    from sapl.protocoloadm.models import pode_ver_documento_adm

    seen = set() if seen is None else seen
    key = (instance._meta.label_lower, instance.pk)
    if key in seen:
        return True, None
    seen.add(key)
    label = instance._meta.label_lower
    if label == 'protocoloadm.documentoadministrativo':
        # AppConfig.attr creates a default row on a cache miss. Historical
        # inspection (especially --dry-run) must never create configuration.
        from sapl.base.models import AppConfig
        mode = document_mode
        if mode is None:
            mode = (AppConfig.objects.using(instance._state.db or 'default')
                    .values_list('documentos_administrativos', flat=True)
                    .first()) or 'O'
        return (pode_ver_documento_adm(AnonymousUser(), instance, modo=mode),
                None)
    if label == 'sessao.sessaoplenaria':
        # Use the same predicate as restringe_sessoes_visiveis, including the
        # legacy NULL value. Work on the snapshot, not the current DB row.
        public = (instance.publicar_pauta or instance.iniciada is not False or
                  instance.data_inicio <= timezone.localdate(at))
        return public, None if public else instance
    if label == 'compilacao.textoarticulado':
        return instance.has_view_permission(), None
    if label == 'compilacao.nota' and instance.publicidade != instance.NPUBL:
        return False, None
    if label == 'compilacao.dispositivo' and not instance.visibilidade:
        return False, None

    pending = None
    for field in instance._meta.concrete_fields:
        if field.is_relation and field.name in OWNER_FIELDS:
            if getattr(instance, field.attname) is None:
                continue
            if history is not None:
                owner = history.get((field.related_model._meta.label_lower,
                                     getattr(instance, field.attname)))
                if owner is None:
                    return False, None
            else:
                try:
                    # Forms and batch objects can retain a cached parent from
                    # before its publication/privacy was changed elsewhere.
                    owner = field.related_model._base_manager.using(
                        instance._state.db or 'default').get(
                            pk=getattr(instance, field.attname))
                except ObjectDoesNotExist:
                    return False, None
            public, scheduled = visibility(
                owner, seen, at=at, history=history,
                document_mode=document_mode)
            if not public and scheduled is None:
                return False, None
            pending = scheduled or pending
    return pending is None, pending


def record(timestamp, origin, object_id, using='default', session=None):
    """A conditional UPDATE makes concurrent writers monotonic."""
    from sapl.base.models import AtualizacaoConteudoPublico

    if timestamp is None:
        return
    key = 'global' if session is None else 'sessao:%s' % session.pk
    rows = AtualizacaoConteudoPublico.objects.using(using)
    # Do not acquire a row lock on every public write before knowing whether
    # it advances the watermark. get_or_create handles the initial race.
    rows.get_or_create(chave=key)
    rows.filter(chave=key).filter(
        Q(timestamp__isnull=True) | Q(timestamp__lt=timestamp)).update(
            timestamp=timestamp, origem=origin, objeto_id=str(object_id),
            disponivel_em=session.data_inicio if session else None)


def register_change(instance, using='default', before=None, deleted=False,
                    timestamp=None):
    if type(instance) not in content_models():
        return
    timestamp = timestamp or timezone.now()
    old_public, old_session = before if before else (False, None)
    public, session = (False, None) if deleted else visibility(instance)
    if old_public or public:
        record(timestamp, instance._meta.label_lower, instance.pk, using)
    elif session or (deleted and old_session and
                     instance._meta.label_lower != 'sessao.sessaoplenaria'):
        record(timestamp, instance._meta.label_lower, instance.pk, using,
               session=session or old_session)

    if instance._meta.label_lower == 'sessao.sessaoplenaria':
        from sapl.base.models import AtualizacaoConteudoPublico
        rows = AtualizacaoConteudoPublico.objects.using(using)
        pending = rows.filter(chave='sessao:%s' % instance.pk)
        if public or deleted:
            pending.delete()
        elif session:
            # A postponed hidden session must not become visible on its old
            # date, even when its latest child event is newer than this save.
            pending.update(disponivel_em=session.data_inicio)


def last_public_update(using='default'):
    from sapl.base.models import AtualizacaoConteudoPublico
    return AtualizacaoConteudoPublico.objects.using(using).filter(
        Q(chave='global') | Q(disponivel_em__lte=timezone.localdate())
    ).exclude(timestamp__isnull=True).order_by('-timestamp').values_list(
        'timestamp', flat=True).first()


def before_save(sender, instance, raw=False, using='default', **kwargs):
    if sender._meta.label_lower == 'base.appconfig' and not raw:
        instance._public_config_before = sender.objects.using(using).\
            values_list('documentos_administrativos', flat=True).first() or 'O'
    if raw or sender not in content_models():
        return
    update_fields = kwargs.get('update_fields')
    values = public_values(instance)
    instance._public_upload = any(
        isinstance(field, FileField) and field.attname in values and
        (update_fields is None or field.name in update_fields) and
        not getattr(instance, field.name)._committed
        for field in instance._meta.concrete_fields)
    old = sender._base_manager.using(using).filter(pk=instance.pk).first() \
        if instance.pk is not None else None
    instance._public_before = (public_values(old), visibility(old)) \
        if old is not None else (None, (False, None))


def after_save(sender, instance, raw=False, using='default', **kwargs):
    if sender._meta.label_lower == 'base.appconfig' and not raw:
        mode = sender.objects.using(using).values_list(
            'documentos_administrativos', flat=True).first() or 'O'
        if mode != getattr(instance, '_public_config_before', mode):
            from sapl.protocoloadm.models import DocumentoAdministrativo
            if DocumentoAdministrativo.objects.using(using).filter(
                    restrito=False).exists():
                record(timezone.now(), 'base.appconfig', instance.pk, using)
    if raw or sender not in content_models():
        return
    previous, visible = getattr(instance, '_public_before', (None, None))
    # update_fields may leave unsaved attributes on the Python instance.
    current = sender._base_manager.using(using).get(pk=instance.pk)
    if (previous is None or previous != public_values(current) or
            getattr(instance, '_public_upload', False)):
        register_change(current, using, before=visible)


def before_delete(sender, instance, using='default', **kwargs):
    if sender._meta.label_lower == 'base.appconfig':
        before_save(sender, instance, using=using)
    if sender in content_models():
        instance._public_delete = visibility(instance)


def after_delete(sender, instance, using='default', **kwargs):
    if sender._meta.label_lower == 'base.appconfig':
        after_save(sender, instance, using=using)
    if sender in content_models():
        register_change(instance, using,
                        before=getattr(instance, '_public_delete', None),
                        deleted=True)


def related_change(sender, instance, action, pk_set=None, using='default',
                   **kwargs):
    if type(instance) not in content_models():
        return
    # Explicit through models are handled by save/delete. Owners and other
    # private memberships must not advance the public timestamp.
    relations = [f for f in instance._meta.get_fields()
                 if f.many_to_many and
                 (getattr(f, 'through', None) or
                  getattr(f.remote_field, 'through', None)) == sender]
    if not relations or any(f.name in ('owners', 'editors', 'perfis')
                            for f in relations):
        return
    if action in ('pre_clear', 'pre_remove'):
        changed = False
        for field in relations:
            name = (field.get_accessor_name() if field.auto_created
                    else field.name)
            related = getattr(instance, name).using(using)
            if action == 'pre_remove':
                related = related.filter(pk__in=pk_set)
            changed = changed or related.exists()
        instance._public_m2m_removed = changed
    if (action == 'post_add' and pk_set or
            action in ('post_clear', 'post_remove') and
            getattr(instance, '_public_m2m_removed', False)):
        register_change(instance, using)


def atomic_write(method):
    """Keep model writes and their signal evidence in the same transaction.

    QuerySet.delete already opens a transaction; ordinary Model.save does
    not. Wrap only registered content models, preserving their custom save
    signatures, upload handling and selected database.
    """
    if getattr(method, '_public_content_atomic', False):
        return method
    parameters = signature(method)

    @wraps(method)
    def write(instance, *args, **kwargs):
        bound = parameters.bind(instance, *args, **kwargs)
        using = bound.arguments.get('using') or router.db_for_write(
            type(instance), instance=instance)
        with transaction.atomic(using=using):
            return method(instance, *args, **kwargs)

    write._public_content_atomic = True
    return write


def connect():
    for model in content_models() | {apps.get_model('base', 'AppConfig')}:
        model.save = atomic_write(model.save)
        model.delete = atomic_write(model.delete)
    pre_save.connect(before_save, dispatch_uid='public_content_before_save')
    post_save.connect(after_save, dispatch_uid='public_content_after_save')
    pre_delete.connect(before_delete,
                       dispatch_uid='public_content_before_delete')
    post_delete.connect(after_delete,
                        dispatch_uid='public_content_after_delete')
    m2m_changed.connect(related_change, dispatch_uid='public_content_m2m')


def bulk_create_public(manager, objects, **kwargs):
    objects = list(objects)
    with transaction.atomic(using=manager.db):
        if kwargs.get('ignore_conflicts') and objects:
            # Django 2.2 does not return inserted IDs with ignore_conflicts.
            # Presence submissions use one unique_together key. get_or_create
            # preserves their conflict handling and emits signals only for
            # actual insertions, so a repeated submission is not an update.
            unique = manager.model._meta.unique_together
            if len(unique) != 1:
                raise ValueError(
                    'ignore_conflicts requires one unique_together key')
            for obj in objects:
                values = {f.attname: getattr(obj, f.attname)
                          for f in obj._meta.concrete_fields
                          if not f.primary_key}
                lookup = {obj._meta.get_field(name).attname:
                          values[obj._meta.get_field(name).attname]
                          for name in unique[0]}
                defaults = {k: v for k, v in values.items() if k not in lookup}
                saved, created = manager.get_or_create(
                    defaults=defaults, **lookup)
                obj.pk = saved.pk
            return objects
        result = manager.bulk_create(objects, **kwargs)
        for obj in objects:
            register_change(obj, manager.db)
    return result


def bulk_update_public(manager, objects, fields, **kwargs):
    objects = list(objects)
    using = manager.db
    with transaction.atomic(using=using):
        previous = {obj.pk: (public_values(obj), visibility(obj))
                    for obj in manager.filter(pk__in=[o.pk for o in objects])}
        result = manager.bulk_update(objects, fields, **kwargs)
        for obj in manager.filter(pk__in=list(previous)):
            values, visible = previous[obj.pk]
            if values != public_values(obj):
                register_change(obj, using, before=visible)
    return result


def update_public(queryset, **values):
    using = queryset.db
    with transaction.atomic(using=using):
        previous = {obj.pk: (public_values(obj), visibility(obj))
                    for obj in queryset}
        result = queryset.update(**values)
        for obj in queryset.model._base_manager.using(using).filter(
                pk__in=list(previous)):
            old, visible = previous[obj.pk]
            if old != public_values(obj):
                register_change(obj, using, before=visible)
    return result
