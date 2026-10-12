from django.contrib.auth import get_user_model
from django.core.cache import cache
from model_bakery import baker
import pytest

from sapl.sessao.models import Orador, SessaoPlenaria


@pytest.fixture(autouse=True)
def limpa_cache_appconfig():
    # o cache em arquivo sobrevive ao rollback do teste
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def sessoes():
    previa = baker.make(SessaoPlenaria, iniciada=False, publicar_pauta=False)
    iniciada = baker.make(SessaoPlenaria, iniciada=True, publicar_pauta=False)
    baker.make(Orador, sessao_plenaria=previa)
    baker.make(Orador, sessao_plenaria=iniciada)
    return previa, iniciada


def _listados(client, endpoint, campo, sessoes):
    """Sessões de `sessoes` referenciadas na listagem completa do endpoint."""
    valores, page = set(), 1
    while page:
        response = client.get('/api/sessao/%s/?page_size=100&page=%s' % (
            endpoint, page))
        assert response.status_code == 200
        dados = response.json()
        valores |= {r[campo] for r in dados['results']}
        page = dados['pagination']['next_page']
    return valores & {s.pk for s in sessoes}


@pytest.mark.django_db(transaction=False)
def test_api_oculta_sessao_previa_do_anonimo(client, sessoes):
    previa, iniciada = sessoes

    assert _listados(client, 'sessaoplenaria', 'id', sessoes) == {
        iniciada.pk}

    assert client.get('/api/sessao/sessaoplenaria/%s/' % previa.pk
                      ).status_code == 404
    assert client.get('/api/sessao/sessaoplenaria/%s/ecidadania/' % previa.pk
                      ).status_code == 404
    assert client.get('/api/sessao/sessaoplenaria/%s/expedientes/' % previa.pk
                      ).status_code == 404
    assert client.get('/api/sessao/sessaoplenaria/%s/expedientes/'
                      % iniciada.pk).status_code == 200

    assert _listados(client, 'orador', 'sessao_plenaria', sessoes) == {
        iniciada.pk}


@pytest.mark.django_db(transaction=False)
def test_api_mostra_sessao_previa_ao_usuario_autenticado(client, sessoes):
    previa, iniciada = sessoes
    client.force_login(baker.make(get_user_model()))

    assert _listados(client, 'sessaoplenaria', 'id', sessoes) == {
        previa.pk, iniciada.pk}
    assert client.get('/api/sessao/sessaoplenaria/%s/' % previa.pk
                      ).status_code == 200
    assert _listados(client, 'orador', 'sessao_plenaria', sessoes) == {
        previa.pk, iniciada.pk}


@pytest.mark.django_db(transaction=False)
def test_media_de_sessao_e_publica(client, settings, sessoes):
    settings.DEBUG = False
    for sessao in sessoes:
        response = client.get(
            '/media/sapl/public/sessaoplenaria/%s/pauta/p.pdf' % sessao.pk)
        assert response.status_code == 200
