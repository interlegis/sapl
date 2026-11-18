import datetime

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from model_bakery import baker
from rest_framework.throttling import AnonRateThrottle

from sapl.api.pagination import StandardPagination
from sapl.api.tests.conftest import resultados
from sapl.base.models import Metadata
from sapl.parlamentares.models import (Legislatura, Mandato, Parlamentar,
                                       Partido)

URL_LEGISLATURA = '/api/parlamentares/legislatura/'
URL_PARTIDO = '/api/parlamentares/partido/'
URL_MANDATO = '/api/parlamentares/mandato/'


@pytest.fixture
def legislaturas(db):
    return [baker.make(Legislatura, numero=n,
                       data_inicio=datetime.date(2000 + 4 * n, 1, 1),
                       data_fim=datetime.date(2003 + 4 * n, 12, 31),
                       data_eleicao=datetime.date(1999 + 4 * n, 10, 1))
            for n in range(1, 4)]


@pytest.fixture
def limite_get_all(monkeypatch):
    monkeypatch.setattr(StandardPagination, 'get_all_max_anonimo', 2)


# get_all


@pytest.mark.django_db(transaction=False)
def test_get_all_anonimo_dentro_do_limite_devolve_lista(api, legislaturas):
    """Usado pela página pública de parlamentares (frontend/parlamentar)."""
    response = api().get(URL_LEGISLATURA, {'get_all': 'true'})

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 3


@pytest.mark.django_db(transaction=False)
def test_get_all_anonimo_acima_do_limite_e_recusado(
        api, legislaturas, limite_get_all):
    response = api().get(URL_LEGISLATURA, {'get_all': 'true'})

    assert response.status_code == 400
    assert 'page_size' in response.json()['detail']


@pytest.mark.django_db(transaction=False)
def test_get_all_anonimo_em_action_acima_do_limite_e_recusado(
        api, legislaturas, limite_get_all):
    legislatura = legislaturas[0]
    for _ in range(3):
        baker.make(Mandato, legislatura=legislatura,
                   data_inicio_mandato=legislatura.data_inicio,
                   data_fim_mandato=legislatura.data_fim)

    url = f'{URL_LEGISLATURA}{legislatura.pk}/parlamentares/'
    assert api().get(url, {'get_all': 'true'}).status_code == 400


@pytest.mark.django_db(transaction=False)
def test_get_all_autenticado_nao_tem_limite(
        api, usuario, legislaturas, limite_get_all):
    response = api(usuario('operador')).get(
        URL_LEGISLATURA, {'get_all': 'true'})

    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.django_db(transaction=False)
def test_paginacao_continua_limitada_sem_get_all(api, legislaturas,
                                                  limite_get_all):
    response = api().get(URL_LEGISLATURA, {'page_size': 2})

    assert response.status_code == 200
    assert response.json()['pagination']['total_entries'] == 3
    assert len(resultados(response)) == 2


# metadata


def _partidos_com_metadata(quantidade):
    content_type = ContentType.objects.get_for_model(Partido)
    partidos = baker.make(Partido, _quantity=quantidade)
    for partido in partidos[::2]:
        baker.make(Metadata, content_type=content_type,
                   object_id=partido.pk, metadata={'sigla_tse': partido.pk})
    return partidos


def _queries(client, url, params):
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url, params)
    assert response.status_code == 200
    return len(queries), response


@pytest.mark.django_db(transaction=False)
def test_metadata_nao_faz_uma_query_por_objeto(api):
    _partidos_com_metadata(30)

    com_2, _ = _queries(api(), URL_PARTIDO, {'page_size': 2})
    com_30, _ = _queries(api(), URL_PARTIDO, {'page_size': 30})
    get_all, _ = _queries(api(), URL_PARTIDO, {'get_all': 'true'})

    assert com_30 == com_2
    assert get_all <= com_2


@pytest.mark.django_db(transaction=False)
def test_metadata_continua_correto(api):
    partidos = _partidos_com_metadata(5)
    id__in = ','.join(str(p.pk) for p in partidos)

    for params in ({'page_size': 5}, {'get_all': 'true'}):
        response = api().get(URL_PARTIDO, {'id__in': id__in, **params})
        metadata = {p['id']: p['metadata'] for p in resultados(response)}
        assert metadata == {
            p.pk: ({'sigla_tse': p.pk} if i % 2 == 0 else {})
            for i, p in enumerate(partidos)}

    detalhe = api().get(f'{URL_PARTIDO}{partidos[0].pk}/').json()
    assert detalhe['metadata'] == {'sigla_tse': partidos[0].pk}


# ordenação (o)


@pytest.fixture
def mandatos(db):
    """Ordem padrão (por parlamentar) diferente da ordem por CPF."""
    ana = baker.make(Parlamentar, nome_parlamentar='Ana', cpf='99999999999')
    bruno = baker.make(Parlamentar, nome_parlamentar='Bruno',
                       cpf='11111111111')
    return [baker.make(Mandato, parlamentar=ana),
            baker.make(Mandato, parlamentar=bruno)]


def _ordem(response):
    assert response.status_code == 200
    return [m['id'] for m in resultados(response)]


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('o', [
    'parlamentar__cpf',
    '-parlamentar__data_nascimento',
    'parlamentar__user__password',
    '?',
    'campo_inexistente',
    'id,parlamentar__cpf',
])
def test_ordenacao_so_aceita_campos_do_proprio_model(api, mandatos, o):
    padrao = _ordem(api().get(URL_MANDATO))

    assert _ordem(api().get(URL_MANDATO, {'o': o})) == padrao


@pytest.mark.django_db(transaction=False)
def test_ordenacao_por_campos_do_proprio_model(api, mandatos):
    ana, bruno = mandatos

    assert _ordem(api().get(URL_MANDATO, {'o': '-id'})) == [bruno.pk, ana.pk]
    assert _ordem(api().get(URL_MANDATO, {'o': 'pk'})) == [ana.pk, bruno.pk]
    assert _ordem(api().get(
        URL_MANDATO, {'o': '-parlamentar_id, id'})) == [bruno.pk, ana.pk]
    assert _ordem(api().get(
        URL_MANDATO, {'o': '-parlamentar'})) == [bruno.pk, ana.pk]


# throttling


@pytest.fixture
def limite_requisicoes(monkeypatch):
    monkeypatch.setattr(AnonRateThrottle, 'THROTTLE_RATES', {'anon': '3/min'})


@pytest.mark.django_db(transaction=False)
def test_requisicoes_anonimas_sao_limitadas(api, legislaturas,
                                            limite_requisicoes):
    client = api()
    status = [client.get(URL_LEGISLATURA).status_code for _ in range(4)]

    assert status == [200, 200, 200, 429]


@pytest.mark.django_db(transaction=False)
def test_requisicoes_autenticadas_nao_sao_limitadas(
        api, usuario, legislaturas, limite_requisicoes):
    client = api(usuario('operador'))

    assert {client.get(URL_LEGISLATURA).status_code
            for _ in range(5)} == {200}


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('url', ['/health/', '/ready/', '/version/'])
def test_health_check_nao_e_limitado(api, limite_requisicoes, url):
    client = api()

    assert 429 not in {client.get(url).status_code for _ in range(5)}
