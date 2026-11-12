"""
Nos models com data de atualização (data_ultima_atualizacao ou
ultima_edicao), o LastModifiedDecorator (sapl/api/views.py) calcula o
Last-Modified antes do dispatch do DRF, aplicando os mesmos filtros da
listagem.
"""
from datetime import datetime, timezone

import pytest
from model_bakery import baker

from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa


pytestmark = pytest.mark.django_db


@pytest.fixture(params=['anonimo', 'autenticado'])
def cliente(request, api, usuario):
    if request.param == 'anonimo':
        return api()
    return api(usuario('operador'))


@pytest.mark.parametrize('url, params', [
    pytest.param('/api/materia/materialegislativa/', {'tipo': 'abc'},
                 id='fk-com-valor-que-nao-e-id'),
    pytest.param('/api/sessao/sessaoplenaria/', {'correspondencias': 999999},
                 id='m2m-com-id-inexistente'),
    pytest.param('/api/norma/normajuridica/', {'data': '2020-13-45'},
                 id='data-invalida'),
])
def test_filtro_invalido_responde_400(cliente, url, params):
    response = cliente.get(url, params)

    assert response.status_code == 400
    assert set(response.json()) == set(params)
    assert not response.has_header('Last-Modified')


def test_last_modified_da_listagem_considera_os_filtros(api):
    tipo, outro_tipo = baker.make(TipoMateriaLegislativa, _quantity=2)
    materia = baker.make(MateriaLegislativa, tipo=tipo)
    outra = baker.make(MateriaLegislativa, tipo=outro_tipo)
    # data_ultima_atualizacao tem auto_now: só o update() grava outra data
    MateriaLegislativa.objects.filter(pk=materia.pk).update(
        data_ultima_atualizacao=datetime(2024, 1, 2, 3, 4, 5,
                                         tzinfo=timezone.utc))
    MateriaLegislativa.objects.filter(pk=outra.pk).update(
        data_ultima_atualizacao=datetime(2024, 6, 7, 8, 9, 10,
                                         tzinfo=timezone.utc))
    url = '/api/materia/materialegislativa/'

    response = api().get(url, {'tipo': tipo.pk})
    assert response.status_code == 200
    assert response['Last-Modified'] == 'Tue, 02 Jan 2024 03:04:05 GMT'

    response = api().get(url)
    assert response.status_code == 200
    assert response['Last-Modified'] == 'Fri, 07 Jun 2024 08:09:10 GMT'

    response = api().get(
        url, {'tipo': tipo.pk},
        HTTP_IF_MODIFIED_SINCE='Tue, 02 Jan 2024 03:04:05 GMT')
    assert response.status_code == 304
