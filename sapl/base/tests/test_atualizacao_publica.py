from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import close_old_connections, transaction
from django.template.loader import render_to_string
from django.utils import timezone
from model_bakery import baker

from sapl.base import atualizacao
from sapl.base.models import (AppConfig, AtualizacaoConteudoPublico, AuditLog,
                              CasaLegislativa)
from sapl.context_processors import public_content_update
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import Orador, SessaoPlenaria, SessaoPlenariaPresenca


BASE = timezone.make_aware(datetime(2026, 11, 16, 12), timezone.utc)
NEXT = BASE + timedelta(days=1)


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    cache.clear()
    monkeypatch.setattr(timezone, 'now', lambda: BASE)
    yield
    cache.clear()


def reset():
    AtualizacaoConteudoPublico.objects.all().delete()
    atualizacao.record(BASE, 'base.casalegislativa', '1')


def advance(monkeypatch):
    monkeypatch.setattr(timezone, 'now', lambda: NEXT)


@pytest.mark.django_db
def test_global_changes_across_modules_and_deletion(monkeypatch):
    norma = baker.make(NormaJuridica)
    casa = baker.make(CasaLegislativa)
    reset()
    advance(monkeypatch)
    norma.ementa = 'Nova redação'
    norma.save()
    assert atualizacao.last_public_update() == NEXT
    evidence = AtualizacaoConteudoPublico.objects.get(chave='global')
    assert evidence.origem == 'norma.normajuridica'
    assert evidence.objeto_id == str(norma.pk)
    assert public_content_update(None)['data_atualizacao_publica'] == NEXT
    monkeypatch.setattr(timezone, 'now', lambda: NEXT + timedelta(days=1))
    casa.delete()
    assert atualizacao.last_public_update() == NEXT + timedelta(days=1)


@pytest.mark.django_db
def test_reads_and_technical_writes_do_not_advance_date(monkeypatch):
    norma = baker.make(NormaJuridica)
    reset()
    advance(monkeypatch)
    baker.make(get_user_model())
    baker.make('norma.NormaEstatisticas', norma=norma)
    for unused in range(2):
        assert public_content_update(None)['data_atualizacao_publica'] == BASE
    assert atualizacao.last_public_update() == BASE
    assert not AtualizacaoConteudoPublico.objects.exclude(
        chave='global').exists()


@pytest.mark.django_db
def test_private_fields_noop_and_unsaved_update_fields(monkeypatch):
    parlamentar = baker.make(Parlamentar)
    reset()
    advance(monkeypatch)
    parlamentar.cpf = '12345678900'
    parlamentar.nome_parlamentar = 'Não foi salvo'
    parlamentar.save(update_fields=['cpf'])
    assert atualizacao.last_public_update() == BASE
    parlamentar.refresh_from_db()
    parlamentar.save()
    assert atualizacao.last_public_update() == BASE
    parlamentar.nome_parlamentar = 'Nome público'
    parlamentar.save()
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_restricted_document_and_publication_transitions(monkeypatch):
    baker.make(AppConfig, documentos_administrativos='O')
    document = baker.make(DocumentoAdministrativo, restrito=True)
    reset()
    advance(monkeypatch)
    document.assunto = 'Alteração restrita'
    document.save()
    baker.make('protocoloadm.DocumentoAcessorioAdministrativo',
               documento=document)
    assert atualizacao.last_public_update() == BASE
    document.restrito = False
    document.save()
    assert atualizacao.last_public_update() == NEXT
    reset()
    document.restrito = True
    document.save()
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_document_module_visibility_changes(monkeypatch):
    config = baker.make(AppConfig, documentos_administrativos='O')
    document = baker.make(DocumentoAdministrativo, restrito=False)
    reset()
    advance(monkeypatch)
    config.documentos_administrativos = 'R'
    config.save()
    assert atualizacao.last_public_update() == NEXT
    reset()
    document.assunto = 'Alteração do módulo restrito'
    document.save()
    assert atualizacao.last_public_update() == BASE
    config.documentos_administrativos = 'O'
    config.save()
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_removing_restrictive_configuration_publishes_documents(monkeypatch):
    config = baker.make(AppConfig, documentos_administrativos='R')
    baker.make(DocumentoAdministrativo, restrito=False)
    reset()
    advance(monkeypatch)
    config.delete()
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_private_articulated_text_and_owner_membership(monkeypatch):
    text = baker.make('compilacao.TextoArticulado', privacidade=99)
    owner = baker.make(get_user_model())
    reset()
    advance(monkeypatch)
    text.ementa = 'Texto em elaboração'
    text.save()
    text.owners.add(owner)
    assert atualizacao.last_public_update() == BASE
    text.privacidade = 0
    text.save()
    assert atualizacao.last_public_update() == NEXT
    reset()
    text.owners.clear()
    assert atualizacao.last_public_update() == BASE
    text.privacidade = 99
    text.save()
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_hidden_session_children_and_publication(monkeypatch):
    session = baker.make(SessaoPlenaria,
                         data_inicio=BASE.date() + timedelta(days=7),
                         iniciada=False, publicar_pauta=False)
    speaker = baker.make(Orador, sessao_plenaria=session)
    reset()
    advance(monkeypatch)
    speaker.observacao = 'Texto público futuro'
    speaker.save()
    assert atualizacao.last_public_update() == BASE
    assert AtualizacaoConteudoPublico.objects.get(
        chave='sessao:%s' % session.pk).timestamp == NEXT
    session.publicar_pauta = True
    session.save()
    assert atualizacao.last_public_update() == NEXT
    assert not AtualizacaoConteudoPublico.objects.filter(
        chave='sessao:%s' % session.pk).exists()


@pytest.mark.django_db
def test_child_uses_current_parent_visibility(monkeypatch):
    session = baker.make(SessaoPlenaria,
                         data_inicio=BASE.date() + timedelta(days=7),
                         iniciada=False, publicar_pauta=False)
    speaker = baker.make(Orador, sessao_plenaria=session)
    published = SessaoPlenaria.objects.get(pk=session.pk)
    published.publicar_pauta = True
    published.save()
    reset()
    advance(monkeypatch)
    speaker.observacao = 'Alteração após publicação'
    speaker.save()
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_session_becomes_public_by_date_without_new_timestamp(monkeypatch):
    session = baker.make(SessaoPlenaria,
                         data_inicio=BASE.date() + timedelta(days=7),
                         iniciada=False, publicar_pauta=False)
    reset()
    advance(monkeypatch)
    session.hora_inicio = '15:00'
    session.save()
    assert atualizacao.last_public_update() == BASE
    monkeypatch.setattr(timezone, 'now', lambda: BASE + timedelta(days=8))
    assert atualizacao.last_public_update() == NEXT
    # Reads select the original evidence, never persisting today's date.
    assert AtualizacaoConteudoPublico.objects.get(
        chave='global').timestamp == BASE


@pytest.mark.django_db
def test_postponed_and_deleted_hidden_sessions(monkeypatch):
    session = baker.make(SessaoPlenaria,
                         data_inicio=BASE.date() + timedelta(days=7),
                         iniciada=False, publicar_pauta=False)
    reset()
    advance(monkeypatch)
    session.data_inicio += timedelta(days=7)
    session.save()
    monkeypatch.setattr(timezone, 'now', lambda: BASE + timedelta(days=8))
    assert atualizacao.last_public_update() == BASE
    session.delete()
    monkeypatch.setattr(timezone, 'now', lambda: BASE + timedelta(days=20))
    assert atualizacao.last_public_update() == BASE


@pytest.mark.django_db
def test_bulk_presence_and_order_changes(monkeypatch):
    session = baker.make(SessaoPlenaria, iniciada=True)
    parlamentar = baker.make(Parlamentar)
    reset()
    advance(monkeypatch)
    atualizacao.bulk_create_public(SessaoPlenariaPresenca.objects, [
        SessaoPlenariaPresenca(
            sessao_plenaria=session, parlamentar=parlamentar)])
    assert atualizacao.last_public_update() == NEXT
    speaker = baker.make(Orador, sessao_plenaria=session)
    reset()
    speaker.numero_ordem += 1
    atualizacao.bulk_update_public(Orador.objects, [speaker], ['numero_ordem'])
    assert atualizacao.last_public_update() == NEXT
    reset()
    atualizacao.update_public(Orador.objects.filter(pk=speaker.pk),
                              numero_ordem=speaker.numero_ordem + 1)
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_conflicting_presence_submission_is_not_a_public_change(monkeypatch):
    session = baker.make(SessaoPlenaria, iniciada=True)
    parlamentar = baker.make(Parlamentar)
    reset()
    advance(monkeypatch)

    def submit():
        return atualizacao.bulk_create_public(
            SessaoPlenariaPresenca.objects, [SessaoPlenariaPresenca(
                sessao_plenaria=session, parlamentar=parlamentar)],
            ignore_conflicts=True)

    inserted = submit()
    assert inserted[0].pk is not None
    assert atualizacao.last_public_update() == NEXT
    monkeypatch.setattr(timezone, 'now', lambda: NEXT + timedelta(hours=1))
    repeated = submit()
    assert repeated[0].pk == inserted[0].pk
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_hidden_bulk_changes_are_only_visible_when_session_is_public(
        monkeypatch):
    session = baker.make(SessaoPlenaria,
                         data_inicio=BASE.date() + timedelta(days=7),
                         iniciada=False, publicar_pauta=False)
    parlamentar = baker.make(Parlamentar)
    reset()
    advance(monkeypatch)
    atualizacao.bulk_create_public(SessaoPlenariaPresenca.objects, [
        SessaoPlenariaPresenca(
            sessao_plenaria=session, parlamentar=parlamentar)])
    assert atualizacao.last_public_update() == BASE
    monkeypatch.setattr(timezone, 'now', lambda: BASE + timedelta(days=8))
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_replacing_file_under_same_name_advances_date(
        monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    session = baker.make(SessaoPlenaria, iniciada=True)
    session.upload_ata = SimpleUploadedFile('ata.pdf', b'%PDF first')
    session.save()
    filename = session.upload_ata.name
    reset()
    advance(monkeypatch)
    session.upload_ata = SimpleUploadedFile('ata.pdf', b'%PDF replacement')
    session.save()
    assert session.upload_ata.name == filename
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_m2m_add_and_clear(monkeypatch):
    norma = baker.make(NormaJuridica)
    assunto = baker.make('norma.AssuntoNorma')
    reset()
    advance(monkeypatch)
    norma.assuntos.add(assunto)
    assert atualizacao.last_public_update() == NEXT
    reset()
    norma.assuntos.clear()
    assert atualizacao.last_public_update() == NEXT
    reset()
    norma.assuntos.clear()
    assert atualizacao.last_public_update() == BASE
    norma.assuntos.remove(assunto)
    assert atualizacao.last_public_update() == BASE


@pytest.mark.django_db
def test_reverse_m2m_changes(monkeypatch):
    norma = baker.make(NormaJuridica)
    assunto = baker.make('norma.AssuntoNorma')
    reset()
    advance(monkeypatch)
    assunto.normajuridica_set.add(norma)
    assert atualizacao.last_public_update() == NEXT
    reset()
    assunto.normajuridica_set.clear()
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_rollback_restores_both_content_and_indicator(monkeypatch):
    casa = baker.make(CasaLegislativa)
    reset()
    advance(monkeypatch)
    with pytest.raises(RuntimeError), transaction.atomic():
        casa.nome = 'Alteração que será desfeita'
        casa.save()
        assert atualizacao.last_public_update() == NEXT
        raise RuntimeError('rollback')
    assert atualizacao.last_public_update() == BASE
    casa.refresh_from_db()
    assert casa.nome != 'Alteração que será desfeita'


def test_concurrent_writers_never_reduce_timestamp(
        django_db_setup, django_db_blocker):
    def write(timestamp):
        close_old_connections()
        try:
            atualizacao.record(timestamp, 'norma.normajuridica', '1')
        finally:
            close_old_connections()

    # Real, committed connections are required for this concurrency check.
    # Manage only these evidence rows; a full DB flush re-emits the project's
    # non-idempotent legacy permission-creation post_migrate receivers.
    with django_db_blocker.unblock():
        previous = list(AtualizacaoConteudoPublico.objects.values())
        try:
            reset()
            with ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(write, [NEXT, BASE + timedelta(hours=1)]))
            assert atualizacao.last_public_update() == NEXT
        finally:
            AtualizacaoConteudoPublico.objects.all().delete()
            AtualizacaoConteudoPublico.objects.bulk_create([
                AtualizacaoConteudoPublico(**row) for row in previous])


def test_failed_evidence_rolls_back_autocommit_content(
        django_db_setup, django_db_blocker, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('evidence unavailable')

    with django_db_blocker.unblock():
        monkeypatch.setattr(atualizacao, 'record', fail)
        with pytest.raises(RuntimeError):
            CasaLegislativa.objects.create(nome='Autocommit rollback')
        assert not CasaLegislativa.objects.filter(
            nome='Autocommit rollback').exists()


@pytest.mark.django_db
def test_empty_history_and_local_date_rendering():
    AtualizacaoConteudoPublico.objects.all().delete()
    assert atualizacao.last_public_update() is None
    html = render_to_string('base/atualizacao_conteudo.html',
                            public_content_update(None))
    assert 'indisponível' in html
    assert '16/11/2026' not in html
    with timezone.override('America/Sao_Paulo'):
        html = render_to_string('base/atualizacao_conteudo.html', {
            'data_atualizacao_publica': BASE.replace(hour=1)})
    assert '15/11/2026' in html


@pytest.mark.django_db
def test_seed_dry_run_and_idempotency(monkeypatch):
    baker.make(NormaJuridica)
    AtualizacaoConteudoPublico.objects.all().delete()
    advance(monkeypatch)
    call_command('inicializar_atualizacao_publica', dry_run=True,
                 stdout=StringIO())
    assert atualizacao.last_public_update() is None
    call_command('inicializar_atualizacao_publica', stdout=StringIO())
    assert atualizacao.last_public_update() == BASE
    atualizacao.record(NEXT, 'norma.normajuridica', '1')
    call_command('inicializar_atualizacao_publica', stdout=StringIO())
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_seed_ignores_invalid_and_technical_history():
    AtualizacaoConteudoPublico.objects.all().delete()
    AuditLog.objects.create(
        timestamp=NEXT, operation='U', username='',
        app_name='base', model_name='AppConfig', object_id=1, data=None)
    AuditLog.objects.create(
        timestamp=NEXT, operation='C', username='',
        app_name='norma', model_name='NormaJuridica', object_id=1, data=None)
    call_command('inicializar_atualizacao_publica', stdout=StringIO())
    assert atualizacao.last_public_update() is None


@pytest.mark.django_db
def test_dry_run_does_not_create_missing_configuration():
    # Visibility checks must not call AppConfig.attr's lazy default creation.
    baker.make(DocumentoAdministrativo, restrito=True)
    AppConfig.objects.all().delete()
    before = AtualizacaoConteudoPublico.objects.count()
    call_command('inicializar_atualizacao_publica', dry_run=True,
                 stdout=StringIO())
    assert not AppConfig.objects.exists()
    assert AtualizacaoConteudoPublico.objects.count() == before


@pytest.mark.django_db
def test_seed_never_uses_uncorroborated_auto_now_dates():
    baker.make(NormaJuridica)
    AuditLog.objects.all().delete()
    AtualizacaoConteudoPublico.objects.all().delete()
    call_command('inicializar_atualizacao_publica', stdout=StringIO())
    assert atualizacao.last_public_update() is None


@pytest.mark.django_db
def test_seed_does_not_use_date_of_private_edit(monkeypatch):
    parlamentar = baker.make(Parlamentar)
    advance(monkeypatch)
    parlamentar.cpf = '12345678900'
    parlamentar.save()
    AtualizacaoConteudoPublico.objects.all().delete()
    call_command('inicializar_atualizacao_publica', stdout=StringIO())
    assert atualizacao.last_public_update() == BASE


@pytest.mark.django_db
def test_seed_includes_publication_by_module_configuration(monkeypatch):
    config = baker.make(AppConfig, documentos_administrativos='R')
    baker.make(DocumentoAdministrativo, restrito=False)
    advance(monkeypatch)
    config.documentos_administrativos = 'O'
    config.save()
    AtualizacaoConteudoPublico.objects.all().delete()
    call_command('inicializar_atualizacao_publica', stdout=StringIO())
    assert atualizacao.last_public_update() == NEXT


@pytest.mark.django_db
def test_seed_tolerates_malformed_config_snapshot():
    AuditLog.objects.create(
        timestamp=NEXT, operation='U', username='', app_name='base',
        model_name='AppConfig', object_id=1,
        data={'model': 'base.appconfig', 'pk': 1, 'fields': ['invalid']})
    AtualizacaoConteudoPublico.objects.all().delete()
    call_command('inicializar_atualizacao_publica', stdout=StringIO())
    assert atualizacao.last_public_update() is None


@pytest.mark.django_db
def test_no_public_write_endpoint(client):
    response = client.post('/api/base/atualizacaoconteudopublico/', {})
    assert response.status_code == 404
