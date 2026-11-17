import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from model_bakery import baker
from rest_framework.test import APIClient

from sapl.parlamentares.models import Parlamentar
from sapl.sessao.models import (ExpedienteMateria, OrdemDia,
                                PresencaOrdemDia, RegistroLeitura,
                                RegistroVotacao,
                                SessaoPlenaria, SessaoPlenariaPresenca,
                                TipoResultadoVotacao, VotoParlamentar)


def url(sessao):
    return '/api/sessao/sessaoplenaria/{}/lote/'.format(sessao.pk)


@pytest.fixture
def client(admin_user):
    c = APIClient()
    c.force_authenticate(admin_user)
    return c


@pytest.fixture
def sessao():
    return baker.make(SessaoPlenaria)


@pytest.fixture
def parlamentares():
    return baker.make(Parlamentar, ativo=True, _quantity=3)


@pytest.fixture
def ordem(sessao):
    return baker.make(OrdemDia, sessao_plenaria=sessao, votacao_aberta=True)


@pytest.fixture
def resultado():
    return baker.make(TipoResultadoVotacao, nome='Aprovado', natureza='A')


def post(client, sessao, data):
    return client.post(url(sessao), data, format='json')


def votacao_nominal(ordem, resultado, parlamentares, votos):
    return {
        'ordem': ordem.pk,
        'tipo_resultado_votacao': resultado.pk,
        'votos': [{'parlamentar': p.pk, 'voto': v}
                  for p, v in zip(parlamentares, votos)],
    }


@pytest.mark.django_db(transaction=False)
def test_lote_exige_autenticacao(sessao):
    response = APIClient().post(url(sessao), {}, format='json')
    assert response.status_code in (401, 403)


@pytest.mark.django_db(transaction=False)
def test_lote_sessao_inexistente(client):
    response = client.post('/api/sessao/sessaoplenaria/999999/lote/',
                           {'presencas_sessao': []}, format='json')
    assert response.status_code == 404


@pytest.mark.django_db(transaction=False)
def test_lote_estrutura_invalida(client, sessao):
    assert post(client, sessao, {}).status_code == 400
    assert post(client, sessao, {'votos': []}).status_code == 400
    assert post(client, sessao, {'presencas_sessao': {}}).status_code == 400
    assert post(client, sessao, {'presencas_sessao': [1]}).status_code == 400


@pytest.mark.django_db(transaction=False)
def test_lote_presencas_idempotente(client, sessao, parlamentares):
    data = {
        'presencas_sessao': [{'parlamentar': p.pk} for p in parlamentares],
        'presencas_ordem_dia': [{'parlamentar': parlamentares[0].pk,
                                 'presente': True}],
    }

    response = post(client, sessao, data)
    assert response.status_code == 200
    r = response.json()
    assert [i['status'] for i in r['presencas_sessao']] == ['criado'] * 3
    assert r['presencas_ordem_dia'][0]['status'] == 'criado'
    assert r['resumo']['criado'] == 4
    assert SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria=sessao).count() == 3
    assert SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria=sessao, data_sessao=sessao.data_inicio).count() == 3

    r = post(client, sessao, data).json()
    assert r['resumo']['inalterado'] == 4
    assert r['resumo']['criado'] == 0
    assert SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria=sessao).count() == 3
    assert PresencaOrdemDia.objects.filter(
        sessao_plenaria=sessao).count() == 1


@pytest.mark.django_db(transaction=False)
def test_lote_remove_presenca(client, sessao, parlamentares):
    baker.make(SessaoPlenariaPresenca, sessao_plenaria=sessao,
               parlamentar=parlamentares[0])

    r = post(client, sessao, {'presencas_sessao': [
        {'parlamentar': parlamentares[0].pk, 'presente': False},
        {'parlamentar': parlamentares[1].pk, 'presente': False},
    ]}).json()

    assert [i['status'] for i in r['presencas_sessao']] == [
        'removido', 'inalterado']
    assert not SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria=sessao).exists()


@pytest.mark.django_db(transaction=False)
def test_lote_falha_de_item_nao_impede_os_demais(client, sessao,
                                                 parlamentares):
    r = post(client, sessao, {'presencas_sessao': [
        {'parlamentar': parlamentares[0].pk},
        {'parlamentar': 999999},
        {'parlamentar': 'abc'},
        {'parlamentar': parlamentares[1].pk},
    ]}).json()

    status = [i['status'] for i in r['presencas_sessao']]
    assert status == ['criado', 'erro', 'erro', 'criado']
    assert 'parlamentar' in r['presencas_sessao'][1]['erros']
    assert r['resumo']['erro'] == 2
    assert SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria=sessao).count() == 2


@pytest.mark.django_db(transaction=False)
def test_lote_votacao_nominal(client, sessao, ordem, resultado,
                              parlamentares):
    data = {'votacoes': [votacao_nominal(
        ordem, resultado, parlamentares, ['Sim', 'Sim', 'Não'])]}

    r = post(client, sessao, data).json()
    assert r['votacoes'][0]['status'] == 'criado'

    registro = RegistroVotacao.objects.get(ordem=ordem)
    assert r['votacoes'][0]['id'] == registro.pk
    assert registro.materia_id == ordem.materia_id
    assert (registro.numero_votos_sim, registro.numero_votos_nao,
            registro.numero_abstencoes) == (2, 1, 0)
    assert VotoParlamentar.objects.filter(
        ordem=ordem, votacao=registro).count() == 3

    # Reenvio do mesmo lote não duplica registro nem votos.
    r = post(client, sessao, data).json()
    assert r['votacoes'][0]['status'] == 'inalterado'
    assert RegistroVotacao.objects.filter(ordem=ordem).count() == 1
    assert VotoParlamentar.objects.filter(ordem=ordem).count() == 3


@pytest.mark.django_db(transaction=False)
def test_lote_votacao_nominal_atualiza_votos(client, sessao, ordem,
                                             resultado, parlamentares):
    post(client, sessao, {'votacoes': [votacao_nominal(
        ordem, resultado, parlamentares, ['Sim', 'Sim', 'Não'])]})

    # Último parlamentar deixa a lista; segundo muda o voto.
    r = post(client, sessao, {'votacoes': [votacao_nominal(
        ordem, resultado, parlamentares[:2], ['Sim', 'Abstenção'])]}).json()
    assert r['votacoes'][0]['status'] == 'atualizado'

    registro = RegistroVotacao.objects.get(ordem=ordem)
    assert (registro.numero_votos_sim, registro.numero_votos_nao,
            registro.numero_abstencoes) == (1, 0, 1)
    votos = dict(VotoParlamentar.objects.filter(
        ordem=ordem).values_list('parlamentar_id', 'voto'))
    assert votos == {parlamentares[0].pk: 'Sim',
                     parlamentares[1].pk: 'Abstenção'}


@pytest.mark.django_db(transaction=False)
def test_lote_votacao_invalida_nao_grava_nada(client, sessao, ordem,
                                              resultado, parlamentares):
    item = votacao_nominal(ordem, resultado, parlamentares,
                           ['Sim', 'Talvez', 'Não'])
    r = post(client, sessao, {'votacoes': [item]}).json()
    assert r['votacoes'][0]['status'] == 'erro'
    assert '1' in r['votacoes'][0]['erros']['votos']
    assert not RegistroVotacao.objects.exists()
    assert not VotoParlamentar.objects.exists()

    item = votacao_nominal(ordem, resultado, parlamentares,
                           ['Sim', 'Sim', 'Não'])
    item['numero_votos_sim'] = 3
    r = post(client, sessao, {'votacoes': [item]}).json()
    assert 'numero_votos_sim' in r['votacoes'][0]['erros']
    assert not RegistroVotacao.objects.exists()


@pytest.mark.django_db(transaction=False)
def test_lote_votacao_simbolica_expediente(client, sessao, resultado):
    expediente = baker.make(ExpedienteMateria, sessao_plenaria=sessao)
    item = {'expediente': expediente.pk,
            'tipo_resultado_votacao': resultado.pk,
            'numero_votos_sim': 10, 'numero_votos_nao': 1,
            'numero_abstencoes': 0}

    r = post(client, sessao, {'votacoes': [item]}).json()
    assert r['votacoes'][0]['status'] == 'criado'
    registro = RegistroVotacao.objects.get(expediente=expediente)
    assert registro.ordem is None
    assert registro.numero_votos_sim == 10

    del item['numero_votos_nao']
    r = post(client, sessao, {'votacoes': [item]}).json()
    assert 'numero_votos_nao' in r['votacoes'][0]['erros']


@pytest.mark.django_db(transaction=False)
def test_lote_votacao_alvo_invalido(client, sessao, ordem, resultado):
    outra = baker.make(OrdemDia)
    expediente = baker.make(ExpedienteMateria, sessao_plenaria=sessao)
    r = post(client, sessao, {'votacoes': [
        {'ordem': outra.pk, 'tipo_resultado_votacao': resultado.pk,
         'votos': []},
        {'ordem': ordem.pk, 'expediente': expediente.pk,
         'tipo_resultado_votacao': resultado.pk, 'votos': []},
        {'tipo_resultado_votacao': resultado.pk, 'votos': []},
    ]}).json()
    assert [i['status'] for i in r['votacoes']] == ['erro'] * 3
    assert not RegistroVotacao.objects.exists()


@pytest.mark.django_db(transaction=False)
def test_lote_leitura_expediente(client, sessao):
    expediente = baker.make(ExpedienteMateria, sessao_plenaria=sessao)
    data = {
        'leituras': [{'expediente': expediente.pk, 'observacao': 'Lida'}],
        'expedientes_materia': [{'id': expediente.pk,
                                 'resultado': 'Matéria lida',
                                 'votacao_aberta': False}],
    }

    r = post(client, sessao, data).json()
    assert r['leituras'][0]['status'] == 'criado'
    assert r['expedientes_materia'][0]['status'] == 'atualizado'
    leitura = RegistroLeitura.objects.get(expediente=expediente)
    assert r['leituras'][0]['id'] == leitura.pk
    assert leitura.materia_id == expediente.materia_id
    assert leitura.ordem is None
    assert leitura.observacao == 'Lida'

    # Reenvio não duplica.
    r = post(client, sessao, data).json()
    assert r['leituras'][0]['status'] == 'inalterado'
    assert r['resumo']['erro'] == 0
    assert RegistroLeitura.objects.filter(expediente=expediente).count() == 1

    data['leituras'][0]['observacao'] = 'Lida em plenário'
    r = post(client, sessao, {'leituras': data['leituras']}).json()
    assert r['leituras'][0]['status'] == 'atualizado'
    leitura.refresh_from_db()
    assert leitura.observacao == 'Lida em plenário'


@pytest.mark.django_db(transaction=False)
def test_lote_retira_leitura_e_remove_duplicadas(client, sessao, ordem):
    baker.make(RegistroLeitura, ordem=ordem, materia=ordem.materia,
               _quantity=2)

    r = post(client, sessao, {'leituras': [{'ordem': ordem.pk}]}).json()
    assert r['leituras'][0]['status'] == 'atualizado'
    assert RegistroLeitura.objects.filter(ordem=ordem).count() == 1

    r = post(client, sessao, {'leituras': [
        {'ordem': ordem.pk, 'lida': False}]}).json()
    assert r['leituras'][0]['status'] == 'removido'
    assert not RegistroLeitura.objects.exists()

    r = post(client, sessao, {'leituras': [
        {'ordem': ordem.pk, 'lida': False},
        {'ordem': baker.make(OrdemDia).pk},
    ]}).json()
    assert [i['status'] for i in r['leituras']] == ['inalterado', 'erro']


@pytest.mark.django_db(transaction=False)
def test_lote_atualiza_ordem_dia(client, sessao, ordem, resultado,
                                 parlamentares):
    data = {
        'votacoes': [votacao_nominal(
            ordem, resultado, parlamentares, ['Sim', 'Sim', 'Sim'])],
        'ordens_dia': [{'id': ordem.pk, 'resultado': resultado.nome,
                        'votacao_aberta': False}],
    }
    r = post(client, sessao, data).json()
    assert r['ordens_dia'][0]['status'] == 'atualizado'
    ordem.refresh_from_db()
    assert ordem.resultado == 'Aprovado'
    assert ordem.votacao_aberta is False

    r = post(client, sessao, data).json()
    assert r['ordens_dia'][0]['status'] == 'inalterado'
    assert r['resumo']['erro'] == 0


@pytest.mark.django_db(transaction=False)
def test_lote_ordem_dia_de_outra_sessao(client, sessao):
    outra = baker.make(OrdemDia)
    ordem = baker.make(OrdemDia, sessao_plenaria=sessao)
    r = post(client, sessao, {'ordens_dia': [
        {'id': outra.pk, 'resultado': 'x'},
        {'id': ordem.pk, 'sessao_plenaria': outra.sessao_plenaria_id},
    ]}).json()
    assert [i['status'] for i in r['ordens_dia']] == ['erro', 'erro']
    outra.refresh_from_db()
    ordem.refresh_from_db()
    assert outra.resultado != 'x'
    assert ordem.sessao_plenaria == sessao


@pytest.mark.django_db(transaction=False)
def test_lote_respeita_permissoes_por_bloco(sessao, ordem, resultado,
                                            parlamentares):
    user = get_user_model().objects.create_user(
        username='operador', password='operador')
    user.user_permissions.add(Permission.objects.get(
        codename='add_sessaoplenariapresenca'))
    c = APIClient()
    c.force_authenticate(user)

    r = post(c, sessao, {
        'presencas_sessao': [{'parlamentar': parlamentares[0].pk}],
        'presencas_ordem_dia': [{'parlamentar': parlamentares[0].pk}],
        'votacoes': [votacao_nominal(
            ordem, resultado, parlamentares, ['Sim', 'Sim', 'Sim'])],
    }).json()

    assert r['presencas_sessao'][0]['status'] == 'criado'
    assert r['presencas_ordem_dia'][0]['status'] == 'erro'
    assert 'sessao.add_presencaordemdia' in r['presencas_ordem_dia'][0][
        'erros']
    assert r['votacoes'][0]['status'] == 'erro'
    assert not PresencaOrdemDia.objects.exists()
    assert not RegistroVotacao.objects.exists()
