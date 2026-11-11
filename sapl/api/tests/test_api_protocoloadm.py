import datetime

import pytest
from model_bakery import baker

from sapl.api.tests.conftest import ids
from sapl.base.models import DOC_ADM_OSTENSIVO, DOC_ADM_RESTRITIVO, AppConfig
from sapl.protocoloadm.models import Anexado, DocumentoAdministrativo

URL_ANEXADO = '/api/protocoloadm/anexado/'


def _anexado(principal, anexado):
    return baker.make(Anexado, documento_principal=principal,
                      documento_anexado=anexado,
                      data_anexacao=datetime.date(2026, 1, 1))


@pytest.fixture
def anexados(db):
    publico_1, publico_2, restrito = (
        baker.make(DocumentoAdministrativo, restrito=r)
        for r in (False, False, True))
    return {
        'publicos': _anexado(publico_1, publico_2),
        'principal_restrito': _anexado(restrito, publico_1),
        'anexado_restrito': _anexado(publico_2, restrito),
    }


@pytest.mark.django_db(transaction=False)
def test_anonimo_nao_ve_anexacao_com_documento_restrito(api, anexados):
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)

    response = api().get(URL_ANEXADO)

    assert response.status_code == 200
    assert ids(response) == {anexados['publicos'].pk}

    for chave in ('principal_restrito', 'anexado_restrito'):
        response = api().get(f'{URL_ANEXADO}{anexados[chave].pk}/')
        assert response.status_code == 404, chave


@pytest.mark.django_db(transaction=False)
def test_usuario_conectado_ve_todas_as_anexacoes(api, usuario, anexados):
    """Como em DocumentoAdministrativo: restrito só exige estar conectado."""
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_OSTENSIVO)

    response = api(usuario('servidor')).get(URL_ANEXADO)

    assert response.status_code == 200
    assert ids(response) == {a.pk for a in anexados.values()}


@pytest.mark.django_db(transaction=False)
def test_anexacoes_no_modo_restritivo(api, usuario, anexados):
    baker.make(AppConfig, documentos_administrativos=DOC_ADM_RESTRITIVO)

    assert api().get(URL_ANEXADO).status_code == 401

    leitor = usuario('leitor', 'protocoloadm.list_anexado',
                     'protocoloadm.detail_anexado')
    response = api(leitor).get(URL_ANEXADO)
    assert response.status_code == 200
    assert ids(response) == {a.pk for a in anexados.values()}
