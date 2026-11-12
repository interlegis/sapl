import datetime

import pytest
from django.utils import timezone
from model_bakery import baker

from sapl.api.tests.conftest import ids
from sapl.base.models import DOC_ADM_OSTENSIVO, DOC_ADM_RESTRITIVO, AppConfig
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import Correspondencia, SessaoPlenaria

URL_CORRESPONDENCIA = '/api/sessao/correspondencia/'


def _correspondencia(sessao, numero_ordem, restrito):
    documento = baker.make(DocumentoAdministrativo, restrito=restrito,
                           assunto=f'Assunto do ofício {numero_ordem}')
    return baker.make(Correspondencia, sessao_plenaria=sessao,
                      documento=documento, numero_ordem=numero_ordem,
                      observacao=f'Observação da correspondência '
                                 f'{numero_ordem}')


@pytest.fixture
def correspondencias(db):
    """
    Uma sessão já realizada, com a correspondência de um documento ostensivo
    e a de um documento restrito, e uma sessão futura ainda não iniciada,
    oculta do público, com a correspondência de outro documento ostensivo.
    """
    realizada = baker.make(SessaoPlenaria,
                           data_inicio=datetime.date(2026, 1, 5),
                           iniciada=True)
    futura = baker.make(
        SessaoPlenaria,
        data_inicio=timezone.localdate() + datetime.timedelta(days=30),
        iniciada=False, publicar_pauta=False)
    return {
        'ostensiva': _correspondencia(realizada, 1, restrito=False),
        'restrita': _correspondencia(realizada, 2, restrito=True),
        'sessao_oculta': _correspondencia(futura, 1, restrito=False),
    }


def _detalhe(client, correspondencia):
    return client.get(f'{URL_CORRESPONDENCIA}{correspondencia.pk}/')


@pytest.mark.django_db(transaction=False)
def test_anonimo_no_modo_ostensivo_nao_ve_correspondencia_de_documento_restrito(
        api, correspondencias):
    """Como em CorrespondenciaCrud: o documento restrito oculta a linha."""
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)

    response = api().get(URL_CORRESPONDENCIA)

    assert response.status_code == 200
    assert ids(response) == {correspondencias['ostensiva'].pk}
    assert 'correspondência 2' not in response.content.decode()

    assert _detalhe(api(), correspondencias['ostensiva']).status_code == 200
    for chave in ('restrita', 'sessao_oculta'):
        assert _detalhe(api(), correspondencias[chave]).status_code == 404, \
            chave


@pytest.mark.django_db(transaction=False)
def test_anonimo_no_modo_restritivo_nao_ve_correspondencias(
        api, correspondencias):
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_RESTRITIVO)

    response = api().get(URL_CORRESPONDENCIA)

    assert response.status_code == 200
    assert ids(response) == set()

    for chave, correspondencia in correspondencias.items():
        assert _detalhe(api(), correspondencia).status_code == 404, chave


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('modo', [DOC_ADM_OSTENSIVO, DOC_ADM_RESTRITIVO])
def test_usuario_autenticado_ve_todas_as_correspondencias(
        api, usuario, correspondencias, modo):
    """Na tela, basta estar conectado, sem permissão específica."""
    baker.make(AppConfig, documentos_administrativos=modo)
    client = api(usuario('servidor'))

    response = client.get(URL_CORRESPONDENCIA)

    assert response.status_code == 200
    assert ids(response) == {c.pk for c in correspondencias.values()}

    for chave, correspondencia in correspondencias.items():
        assert _detalhe(client, correspondencia).status_code == 200, chave
