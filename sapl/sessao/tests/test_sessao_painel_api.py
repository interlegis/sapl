from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from sapl.base.models import Autor
from sapl.materia.models import Autoria
from sapl.parlamentares.models import Mandato, Parlamentar
from sapl.sessao.models import (ExpedienteMateria, IntegranteMesa, OrdemDia,
                                OradorExpediente, PresencaOrdemDia,
                                RegistroLeitura, RegistroVotacao,
                                SessaoPlenaria, SessaoPlenariaPresenca,
                                VotoParlamentar)


def url(sessao):
    return '/api/sessao/sessaoplenaria/{}/painel/'.format(sessao.pk)


@pytest.fixture
def sessao():
    return baker.make(SessaoPlenaria, data_inicio=timezone.localdate(),
                      iniciada=True)


@pytest.fixture
def sessao_completa(sessao):
    """Casa com 21 parlamentares e 20 matérias votadas nominalmente."""
    parlamentares = baker.make(Parlamentar, ativo=True, _quantity=21)
    for p in parlamentares:
        baker.make(Mandato, parlamentar=p, legislatura=sessao.legislatura)
        baker.make(SessaoPlenariaPresenca, sessao_plenaria=sessao,
                   parlamentar=p)
        baker.make(PresencaOrdemDia, sessao_plenaria=sessao, parlamentar=p)
    baker.make(IntegranteMesa, sessao_plenaria=sessao,
               parlamentar=parlamentares[0])
    for _ in range(20):
        ordem = baker.make(OrdemDia, sessao_plenaria=sessao)
        baker.make(Autoria, materia=ordem.materia, autor=baker.make(Autor))
        registro = baker.make(RegistroVotacao, ordem=ordem,
                              materia=ordem.materia)
        for p in parlamentares:
            baker.make(VotoParlamentar, ordem=ordem, votacao=registro,
                       parlamentar=p, voto='Sim')
    for _ in range(5):
        expediente = baker.make(ExpedienteMateria, sessao_plenaria=sessao)
        baker.make(RegistroLeitura, expediente=expediente,
                   materia=expediente.materia)
    baker.make(OradorExpediente, sessao_plenaria=sessao,
               parlamentar=parlamentares[1])
    return sessao


@pytest.mark.django_db(transaction=False)
def test_painel_publico_traz_toda_a_sessao(sessao_completa):
    response = APIClient().get(url(sessao_completa))
    assert response.status_code == 200
    r = response.json()

    assert r['sessao_plenaria']['id'] == sessao_completa.pk
    assert r['tipo_sessao']['id'] == sessao_completa.tipo_id
    assert len(r['parlamentares']) == 21
    assert len(r['mandatos']) == 21
    assert len(r['presencas_sessao']) == 21
    assert len(r['presencas_ordem_dia']) == 21
    assert len(r['integrantes_mesa']) == 1
    assert len(r['ordens_dia']) == 20
    assert len(r['expedientes_materia']) == 5
    assert len(r['materias']) == 25
    assert len(r['autorias']) == 20
    assert len(r['autores']) == 20
    assert len(r['registros_votacao']) == 20
    assert len(r['votos']) == 420
    assert len(r['registros_leitura']) == 5
    assert len(r['oradores_expediente']) == 1


@pytest.mark.django_db(transaction=False)
def test_painel_mesmo_formato_da_listagem(sessao_completa):
    c = APIClient()
    painel = c.get(url(sessao_completa)).json()
    lista = c.get('/api/sessao/ordemdia/', {
        'sessao_plenaria': sessao_completa.pk, 'page_size': 100}).json()
    assert sorted(painel['ordens_dia'], key=lambda o: o['id']) == \
        sorted(lista['results'], key=lambda o: o['id'])


@pytest.mark.django_db(transaction=False)
def test_painel_nao_mistura_outras_sessoes(sessao_completa):
    outra = baker.make(SessaoPlenaria, data_inicio=timezone.localdate())
    baker.make(OrdemDia, sessao_plenaria=outra)
    baker.make(SessaoPlenariaPresenca, sessao_plenaria=outra)

    r = APIClient().get(url(outra)).json()
    assert len(r['ordens_dia']) == 1
    assert len(r['presencas_sessao']) == 1
    assert r['votos'] == []


@pytest.mark.django_db(transaction=False)
def test_painel_numero_de_consultas_limitado(sessao_completa):
    with CaptureQueriesContext(connection) as consultas:
        assert APIClient().get(url(sessao_completa)).status_code == 200
    # ~620 registros serializados: o número de consultas não pode crescer
    # com o volume (sem N+1 em __str__, metadata e many-to-many).
    assert len(consultas) < 100


@pytest.mark.django_db(transaction=False)
def test_painel_sessao_futura_oculta_ao_publico(admin_user):
    futura = baker.make(SessaoPlenaria, iniciada=False, publicar_pauta=False,
                        data_inicio=timezone.localdate() + timedelta(days=3))
    assert APIClient().get(url(futura)).status_code == 404

    c = APIClient()
    c.force_authenticate(admin_user)
    assert c.get(url(futura)).status_code == 200


@pytest.mark.django_db(transaction=False)
def test_painel_sessao_inexistente():
    response = APIClient().get('/api/sessao/sessaoplenaria/999999/painel/')
    assert response.status_code == 404
