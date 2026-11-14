"""Envio da pauta da sessão a painel de votação externo.

O que estes testes protegem, em ordem de importância:

1. **A URL de destino vir só da configuração.** Se o corpo da requisição
   voltar a escolher para onde o SAPL faz POST, qualquer usuário logado manda
   o servidor chamar a rede interna.
2. **Desligado, nada muda.** Casa que não usa painel externo não vê botão e
   não ganha rota.
3. **A chave não vaza** — nem na tela, nem na API.
"""
from unittest import mock

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.forms.models import model_to_dict
from django.test import Client
from django.urls import reverse
from model_bakery import baker
import pytest
import requests

from sapl.base.forms import ConfiguracoesAppForm
from sapl.base.models import AppConfig, CasaLegislativa
from sapl.sessao import painel_externo
from sapl.sessao.models import ExpedienteMateria, OrdemDia, SessaoPlenaria

URL_PAINEL = 'https://painel.exemplo.leg.br/api/pauta'
CHAVE = 'chave-do-painel'


@pytest.fixture(autouse=True)
def limpa_cache_appconfig():
    # o cache do AppConfig.attr sobrevive ao rollback do teste
    cache.clear()
    yield
    cache.clear()


def configura(ativo=True, url=URL_PAINEL, api_key=CHAVE):
    config = AppConfig.objects.first() or AppConfig()
    config.painel_externo_ativo = ativo
    config.painel_externo_url = url
    config.painel_externo_api_key = api_key
    config.save()
    cache.clear()
    return config


@pytest.fixture
def sessao(db):
    sessao = baker.make(SessaoPlenaria)
    baker.make(ExpedienteMateria, sessao_plenaria=sessao, tipo_votacao=4)
    baker.make(OrdemDia, sessao_plenaria=sessao, numero_ordem=1,
               tipo_votacao=2)
    return sessao


@pytest.fixture
def operador(db):
    usuario = baker.make('auth.User', username='operador-sessao')
    usuario.user_permissions.add(Permission.objects.get(
        content_type__app_label='sessao', codename='change_sessaoplenaria'))
    cliente = Client()
    cliente.force_login(usuario)
    return cliente


@pytest.fixture
def sem_permissao(db):
    cliente = Client()
    cliente.force_login(baker.make('auth.User', username='qualquer-um'))
    return cliente


def url_envio(sessao):
    return '/api/sessao/sessaoplenaria/%s/materias/enviar/' % sessao.pk


def resposta(status, corpo=None):
    r = mock.Mock(status_code=status, ok=200 <= status < 300)
    r.json.return_value = {} if corpo is None else corpo
    return r


# ------------------------------------------------------------- liga/desliga

@pytest.mark.django_db(transaction=False)
def test_desligado_nao_tem_rota_nem_botao(operador, sessao):
    configura(ativo=False)

    with mock.patch('sapl.sessao.painel_externo.requests.post') as post:
        assert operador.post(url_envio(sessao)).status_code == 404
    post.assert_not_called()

    pagina = operador.get(reverse('sapl.sessao:sessaoplenaria_detail',
                                  kwargs={'pk': sessao.pk}))
    assert 'enviar-pauta-painel' not in pagina.content.decode()


@pytest.mark.django_db(transaction=False)
def test_botao_so_para_quem_opera_a_sessao(operador, sem_permissao, sessao):
    configura()
    detalhe = reverse('sapl.sessao:sessaoplenaria_detail',
                      kwargs={'pk': sessao.pk})

    assert 'enviar-pauta-painel' in operador.get(detalhe).content.decode()
    assert 'enviar-pauta-painel' not in \
        sem_permissao.get(detalhe).content.decode()
    assert 'enviar-pauta-painel' not in Client().get(detalhe).content.decode()


@pytest.mark.django_db(transaction=False)
def test_envio_exige_permissao_de_operar_a_sessao(sem_permissao, sessao):
    configura()

    with mock.patch('sapl.sessao.painel_externo.requests.post') as post:
        assert sem_permissao.post(url_envio(sessao)).status_code == 403
        # anônimo: 401, porque o TokenAuthentication pede credencial
        assert Client().post(url_envio(sessao)).status_code == 401
    post.assert_not_called()


# -------------------------------------------------------------------- envio

@pytest.mark.django_db(transaction=False)
def test_envia_a_pauta_para_a_url_configurada(operador, sessao):
    configura()

    with mock.patch('sapl.sessao.painel_externo.requests.post',
                    return_value=resposta(201, {'message': 'Integrado.'})
                    ) as post:
        r = operador.post(url_envio(sessao))

    assert r.status_code == 200
    assert r.json() == {'ok': True, 'status_remoto': 201,
                        'mensagem': 'Integrado.'}
    args, kwargs = post.call_args
    assert args == (URL_PAINEL,)
    assert kwargs['headers'] == {'X-API-KEY': CHAVE}
    assert kwargs['timeout'] == painel_externo.TIMEOUT
    assert kwargs['json']['sessao'] == sessao.pk


@pytest.mark.django_db(transaction=False)
def test_corpo_da_requisicao_nao_escolhe_destino_nem_chave(operador, sessao):
    configura()

    with mock.patch('sapl.sessao.painel_externo.requests.post',
                    return_value=resposta(201)) as post:
        operador.post(url_envio(sessao),
                      {'url': 'http://169.254.169.254/latest/meta-data',
                       'api_key': 'chave-do-atacante'},
                      content_type='application/json')

    args, kwargs = post.call_args
    assert args == (URL_PAINEL,)
    assert kwargs['headers'] == {'X-API-KEY': CHAVE}


@pytest.mark.django_db(transaction=False)
def test_recusa_do_painel_vira_502_com_a_mensagem_dele(operador, sessao):
    configura()
    recusa = resposta(400, {'message': 'Tipo de sessao nao cadastrado: 9'})

    with mock.patch('sapl.sessao.painel_externo.requests.post',
                    return_value=recusa):
        r = operador.post(url_envio(sessao))

    assert r.status_code == 502
    assert r.json() == {'ok': False, 'status_remoto': 400,
                        'mensagem': 'Tipo de sessao nao cadastrado: 9'}


@pytest.mark.django_db(transaction=False)
def test_falha_de_rede_nao_expoe_detalhe(operador, sessao):
    configura()
    falha = requests.ConnectionError('recusado por 10.0.0.7:8443')

    with mock.patch('sapl.sessao.painel_externo.requests.post',
                    side_effect=falha):
        r = operador.post(url_envio(sessao))

    assert r.status_code == 502
    assert r.json()['status_remoto'] is None
    assert '10.0.0.7' not in r.content.decode()


@pytest.mark.django_db(transaction=False)
def test_pauta_segue_o_formato_documentado(rf, sessao):
    pauta = painel_externo.montar_pauta(sessao, rf.get('/'))

    assert set(pauta) == {'sessao', 'sessao_nome', 'tipo_sessao',
                          'expediente', 'ordem_dia'}
    assert pauta['tipo_sessao'] == {'id': sessao.tipo_id,
                                    'nome': sessao.tipo.nome}

    item = pauta['ordem_dia'][0]
    assert item['numero_ordem'] == 1
    assert set(item['materia']) == {
        'id_materia', 'nome_documento', 'autoria', 'tipo_materia', 'ementa',
        'status', 'status_sessao', 'status_tramitacao', 'fase_materia',
        'quorum', 'tipo_votacao', 'pdf_url', 'tramitacao_pdf_url'}
    assert item['materia']['tipo_votacao'] == 'Nominal'
    assert pauta['expediente'][0]['materia']['tipo_votacao'] == 'Leitura'


# ---------------------------------------------------- tela de configuração

def dados_do_form(config, **campos):
    dados = {nome: valor for nome, valor in model_to_dict(
        config, fields=ConfiguracoesAppForm._meta.fields).items()
        if valor is not None}
    dados.update(campos)
    return dados


@pytest.mark.django_db(transaction=False)
def test_ligar_exige_url_e_chave():
    baker.make(CasaLegislativa)
    config = configura(ativo=False, url='', api_key='')

    form = ConfiguracoesAppForm(
        instance=config, data=dados_do_form(config, painel_externo_ativo=True))

    assert not form.is_valid()
    assert 'painel_externo_url' in form.errors
    assert 'painel_externo_api_key' in form.errors


@pytest.mark.django_db(transaction=False)
def test_chave_em_branco_mantem_a_salva_e_nao_aparece_na_tela():
    baker.make(CasaLegislativa)
    config = configura()

    form = ConfiguracoesAppForm(
        instance=config, data=dados_do_form(config, painel_externo_api_key=''))
    assert form.is_valid(), form.errors
    form.save()

    config.refresh_from_db()
    assert config.painel_externo_api_key == CHAVE
    assert CHAVE not in str(
        ConfiguracoesAppForm(instance=config)['painel_externo_api_key'])


@pytest.mark.django_db(transaction=False)
def test_api_do_appconfig_nao_expoe_a_chave(admin_client):
    configura()

    r = admin_client.get('/api/base/appconfig/')

    assert r.status_code == 200
    assert 'painel_externo_url' in r.content.decode()
    assert CHAVE not in r.content.decode()
