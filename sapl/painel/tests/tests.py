import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from sapl.base.models import AppConfig as ConfiguracoesAplicacao
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import (Legislatura, Mandato, Parlamentar,
                                       SessaoLegislativa, Votante)
from sapl.sessao.models import (OrdemDia, PresencaOrdemDia, SessaoPlenaria,
                                TipoResultadoVotacao, TipoSessaoPlenaria,
                                VotoParlamentar)

NOMINAL = 2
LEITURA = 4


def _sessao_plenaria():
    legislatura = baker.make(Legislatura)
    sessao_legislativa = baker.make(SessaoLegislativa)
    tipo = baker.make(TipoSessaoPlenaria)
    return baker.make(SessaoPlenaria, legislatura=legislatura,
                      sessao_legislativa=sessao_legislativa, tipo=tipo, numero=1)


def _materia():
    tipo_materia = baker.make(TipoMateriaLegislativa)
    return baker.make(MateriaLegislativa, tipo=tipo_materia)


def _ordem_nominal_aberta(registro_aberto=False):
    sessao = _sessao_plenaria()
    materia = _materia()
    ordem = baker.make(OrdemDia, sessao_plenaria=sessao, materia=materia,
                       tipo_votacao=NOMINAL, votacao_aberta=True,
                       registro_aberto=registro_aberto)
    return sessao, ordem


def _ordem_leitura_aberta():
    sessao = _sessao_plenaria()
    materia = _materia()
    ordem = baker.make(OrdemDia, sessao_plenaria=sessao, materia=materia,
                       tipo_votacao=LEITURA, votacao_aberta=True)
    return sessao, ordem


def _votante(sessao, admin_user):
    parlamentar = baker.make(Parlamentar, ativo=True)
    baker.make(PresencaOrdemDia, sessao_plenaria=sessao, parlamentar=parlamentar)
    baker.make(Votante, parlamentar=parlamentar, user=admin_user)
    return parlamentar


def _votante_com_client(sessao):
    """
    Como _votante(), mas cria seu próprio usuário (não-superuser, só com a
    permissão parlamentares.can_vote) e devolve um Client logado separado —
    necessário para testar a corrida entre o operador e o vereador, que
    precisam ser duas sessões/usuários distintos.
    """
    parlamentar = baker.make(Parlamentar, ativo=True)
    baker.make(PresencaOrdemDia, sessao_plenaria=sessao, parlamentar=parlamentar)
    user = get_user_model().objects.create_user(
        username='votante-{}'.format(parlamentar.pk), password='x')
    user.user_permissions.add(Permission.objects.get(codename='can_vote'))
    baker.make(Votante, parlamentar=parlamentar, user=user)
    client = Client()
    client.force_login(user)
    return parlamentar, client


def _registrar_url(sessao, ordem):
    return reverse('sapl.sessao:votacaonominal',
                   kwargs={'pk': sessao.pk, 'oid': ordem.pk, 'mid': ordem.materia_id})


@pytest.mark.django_db(transaction=False)
def test_votante_view_envia_headers_never_cache(admin_client, admin_user):
    sessao, ordem = _ordem_nominal_aberta()
    _votante(sessao, admin_user)

    response = admin_client.get(reverse('sapl.painel:voto_individual'))

    assert response.status_code == 200
    assert 'no-store' in response['Cache-Control']


@pytest.mark.django_db(transaction=False)
def test_votante_view_mostra_materia_quando_registro_fechado(admin_client, admin_user):
    sessao, ordem = _ordem_nominal_aberta(registro_aberto=False)
    _votante(sessao, admin_user)

    response = admin_client.get(reverse('sapl.painel:voto_individual'))

    assert response.status_code == 200
    assert 'error_message' not in response.context
    assert response.context['materia'] == ordem.materia


@pytest.mark.django_db(transaction=False)
def test_votante_view_mostra_erro_explicito_quando_registro_bloqueado(admin_client, admin_user):
    """
    Regressão da causa raiz #1: quando a Mesa bloqueia novos votos
    (registro_aberto=True), o vereador que ainda não votou precisa ver uma
    mensagem explícita — não uma tela em branco sem explicação.
    """
    sessao, ordem = _ordem_nominal_aberta(registro_aberto=True)
    _votante(sessao, admin_user)

    response = admin_client.get(reverse('sapl.painel:voto_individual'))

    assert response.status_code == 200
    assert 'Mesa encerrou o recebimento de novos votos' in response.context['error_message']


@pytest.mark.django_db(transaction=False)
def test_voto_do_vereador_prevalece_sobre_lote_do_operador(admin_client):
    """
    Invariante: o voto do próprio vereador sempre prevalece sobre qualquer
    valor provisório já existente para ele (ex.: de uma tentativa anterior
    do operador, ou de qualquer outra origem). Complementa
    test_salvar_votacao_nao_sobrescreve_voto_ja_registrado (que cobre a
    ordem inversa: o operador não pode sobrescrever um voto real já
    registrado) — aqui é o vereador votando por cima de um valor existente
    através da view de verdade, não apenas o estado inicial simulado.
    """
    sessao, ordem = _ordem_nominal_aberta()
    vereador, votante_client = _votante_com_client(sessao)

    # 1) Já existe um valor provisório "Não Votou" para o vereador (ex.: o
    #    <select> nunca foi tocado pelo operador). Esse valor nunca deveria
    #    impedir o vereador de votar de verdade.
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=vereador,
               voto='Não Votou')

    # 2) O vereador vota pelo tablet — seu voto real prevalece sobre o
    #    valor provisório.
    response = votante_client.post(
        reverse('sapl.painel:voto_individual'), {'voto': 'Sim'})
    assert response.status_code == 302

    voto = VotoParlamentar.objects.get(ordem=ordem, parlamentar=vereador)
    assert voto.voto == 'Sim'


@pytest.mark.django_db(transaction=False)
def test_post_de_voto_bloqueado_nao_persiste(admin_client, admin_user):
    sessao, ordem = _ordem_nominal_aberta(registro_aberto=True)
    parlamentar = _votante(sessao, admin_user)

    response = admin_client.post(
        reverse('sapl.painel:voto_individual'), {'voto': 'Sim'})

    assert response.status_code == 302
    assert not VotoParlamentar.objects.filter(
        ordem=ordem, parlamentar=parlamentar).exists()


@pytest.mark.django_db(transaction=False)
def test_post_rejeita_valor_de_voto_invalido(admin_client, admin_user):
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _votante(sessao, admin_user)

    response = admin_client.post(
        reverse('sapl.painel:voto_individual'), {'voto': 'Outro'})

    assert response.status_code == 302
    assert not VotoParlamentar.objects.filter(
        ordem=ordem, parlamentar=parlamentar).exists()


@pytest.mark.django_db(transaction=False)
def test_propria_tela_nao_mostra_voto_de_outra_materia(admin_client):
    """
    Regressão: votacao() buscava o voto do próprio vereador com
    Q(ordem=ordem_dia) | Q(expediente=expediente) — quando a matéria atual
    é uma OrdemDia, expediente é None, e Q(expediente=None) vira
    "expediente_id IS NULL" no SQL, que é verdadeiro para QUALQUER voto de
    ordem do dia daquele vereador, não só o desta matéria (idem para
    ExpedienteMateria, cujas votações também têm ordem=None). Com .first()
    sem ordenação, o vereador podia ver o voto de uma matéria antiga em vez
    do voto (ou ausência de voto) da matéria atual — inclusive depois de
    trocar o próprio voto, já que a query buscava a linha errada.
    """
    sessao, ordem_antiga = _ordem_nominal_aberta()
    vereador, votante_client = _votante_com_client(sessao)
    baker.make(VotoParlamentar, ordem=ordem_antiga, parlamentar=vereador, voto='Sim')

    ordem_antiga.votacao_aberta = False
    ordem_antiga.save()
    baker.make(OrdemDia, sessao_plenaria=sessao, materia=_materia(),
               tipo_votacao=NOMINAL, votacao_aberta=True, registro_aberto=False)
    baker.make(PresencaOrdemDia, sessao_plenaria=sessao, parlamentar=vereador)

    status_url = reverse('sapl.painel:voto_individual_status')

    # Ainda não votou na matéria atual — não pode herdar o 'Sim' da antiga.
    assert votante_client.get(status_url).json()['voto_parlamentar'] is None

    votante_client.post(reverse('sapl.painel:voto_individual'), {'voto': 'Não'})

    assert votante_client.get(status_url).json()['voto_parlamentar'] == 'Não'
    assert VotoParlamentar.objects.get(
        ordem=ordem_antiga, parlamentar=vereador).voto == 'Sim'


@pytest.mark.django_db(transaction=False)
def test_get_dados_painel_nao_usa_etag_incompleto(admin_client):
    baker.make(ConfiguracoesAplicacao, mostrar_voto=True, mostrar_brasao_painel=False)
    sessao, ordem = _ordem_nominal_aberta()
    url = reverse('sapl.painel:dados_painel', kwargs={'pk': sessao.pk})

    primeira = admin_client.get(url)
    assert primeira.status_code == 200
    assert 'ETag' not in primeira

    # Mesmo que um cliente antigo ainda envie o último valor conhecido, a
    # resposta deve ser sempre recalculada para não ocultar mudanças em
    # presenças, oradores ou configuração do painel.
    segunda = admin_client.get(url, HTTP_IF_NONE_MATCH='"valor-antigo"')
    assert segunda.status_code == 200
    assert 'ETag' not in segunda


@pytest.mark.django_db(transaction=False)
def test_painel_exibe_nao_votou_para_parlamentar_sem_voto(admin_client):
    """
    Regressão: depois que o fechamento deixou de persistir o valor
    provisório "Não Votou", parlamentares sem VotoParlamentar passaram a
    chegar ao painel como null. O JavaScript não pode renderizar esse null
    literalmente no telão.
    """
    baker.make(ConfiguracoesAplicacao, mostrar_voto=True,
               mostrar_brasao_painel=False)
    sessao, ordem = _ordem_nominal_aberta()
    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Aprovada',
                                natureza='A')
    votou = baker.make(Parlamentar, ativo=True)
    nao_votou = baker.make(Parlamentar, ativo=True)
    for parlamentar in (votou, nao_votou):
        baker.make(PresencaOrdemDia, sessao_plenaria=sessao,
                   parlamentar=parlamentar)
        baker.make(Mandato, parlamentar=parlamentar,
                   legislatura=sessao.legislatura)

    resposta_registro = admin_client.post(_registrar_url(sessao, ordem), {
        'salvar-votacao': '1',
        'resultado_votacao': str(tipo_resultado.pk),
        'observacao': '',
        'voto_parlamentar': [
            'Sim:{}'.format(votou.pk),
            'Não Votou:{}'.format(nao_votou.pk),
        ],
    })
    assert resposta_registro.status_code == 302

    dados = admin_client.get(reverse(
        'sapl.painel:dados_painel', kwargs={'pk': sessao.pk})).json()
    parlamentar_sem_voto = next(
        p for p in dados['presentes'] if p['parlamentar_id'] == nao_votou.pk)
    assert parlamentar_sem_voto['voto'] is None

    painel = admin_client.get(reverse(
        'sapl.painel:painel_principal', kwargs={'pk': sessao.pk}))
    assert painel.status_code == 200
    assert b'if (!parlamentar.voto)' in painel.content
    assert 'Não votou'.encode() in painel.content


@pytest.mark.django_db(transaction=False)
def test_dados_painel_leitura_nao_tem_voto_individual(admin_client, admin_user):
    """
    Contrato consumido pelo JS do painel (sapl/templates/painel/index.html):
    para uma matéria em Leitura, tipo_votacao chega como a string 'Leitura'
    (não o código inteiro) e nenhum parlamentar presente recebe um voto —
    é isso que permite ao JS distinguir "não há voto individual nesta
    matéria" de "ainda não votou".
    """
    baker.make(ConfiguracoesAplicacao, mostrar_voto=True, mostrar_brasao_painel=False)
    sessao, ordem = _ordem_leitura_aberta()
    _votante(sessao, admin_user)

    dados = admin_client.get(reverse(
        'sapl.painel:dados_painel', kwargs={'pk': sessao.pk})).json()

    assert dados['tipo_votacao'] == 'Leitura'
    assert all(p['voto'] == '' for p in dados['presentes'])


@pytest.mark.django_db(transaction=False)
def test_dados_painel_sem_materia_nao_envia_tipo_votacao(admin_client, admin_user):
    """
    Sem nenhuma matéria aberta ou já votada/lida (ex.: sessão solene), a
    chave tipo_votacao não é enviada — o JS trata isso como "sem voto
    individual" da mesma forma que trata 'Leitura'.
    """
    baker.make(ConfiguracoesAplicacao, mostrar_voto=True, mostrar_brasao_painel=False)
    sessao = _sessao_plenaria()

    dados = admin_client.get(reverse(
        'sapl.painel:dados_painel', kwargs={'pk': sessao.pk})).json()

    assert 'tipo_votacao' not in dados


@pytest.mark.django_db(transaction=False)
def test_votante_status_reflete_estado_e_nao_exige_permissao_do_painel():
    """
    votante_status precisa ser alcançável por uma conta só-Votante (sem
    nenhuma permissão do app painel) — é por isso que não reaproveita
    get_dados_painel, que exige check_permission (permissão de módulo do
    app painel).
    """
    sessao, ordem = _ordem_nominal_aberta()
    vereador, votante_client = _votante_com_client(sessao)

    status_url = reverse('sapl.painel:voto_individual_status')

    resposta = votante_client.get(status_url)
    assert resposta.status_code == 200
    data = resposta.json()
    assert data['materia_id'] == ordem.materia_id
    assert data['status_message'] == 'Aguardando seu voto.'
    assert data['voto_parlamentar'] is None

    votante_client.post(reverse('sapl.painel:voto_individual'), {'voto': 'Não'})

    resposta2 = votante_client.get(status_url)
    data2 = resposta2.json()
    assert data2['voto_parlamentar'] == 'Não'
    assert 'encerramento da votação' in data2['status_message']
