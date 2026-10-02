from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from model_bakery import baker

from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.painel.views import VoteError, _cast_vote, _toggle_registro
from sapl.parlamentares.models import (Legislatura, Parlamentar,
                                       SessaoLegislativa)
from sapl.sessao.models import (OrdemDia, PresencaOrdemDia, RegistroVotacao,
                                SessaoPlenaria, TipoResultadoVotacao,
                                TipoSessaoPlenaria, VotoParlamentar)

NOMINAL = 2


@pytest.fixture(autouse=True)
def in_memory_channel_layer(settings):
    settings.CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}


def _sessao_plenaria():
    legislatura = baker.make(Legislatura)
    sessao_legislativa = baker.make(SessaoLegislativa)
    tipo = baker.make(TipoSessaoPlenaria)
    return baker.make(SessaoPlenaria, legislatura=legislatura,
                      sessao_legislativa=sessao_legislativa, tipo=tipo, numero=1)


def _materia():
    tipo_materia = baker.make(TipoMateriaLegislativa)
    return baker.make(MateriaLegislativa, tipo=tipo_materia)


def _ordem_nominal_aberta():
    sessao = _sessao_plenaria()
    materia = _materia()
    ordem = baker.make(OrdemDia, sessao_plenaria=sessao, materia=materia,
                       tipo_votacao=NOMINAL, votacao_aberta=True,
                       registro_aberto=False)
    return sessao, ordem


def _presente(sessao):
    parlamentar = baker.make(Parlamentar, ativo=True)
    baker.make(PresencaOrdemDia, sessao_plenaria=sessao, parlamentar=parlamentar)
    return parlamentar


# Registro individual de votação nominal (Ordem do Dia e Expediente) é
# feito hoje pela tela v2 (Vue) — votacaonominal_v2, sem oid/mid na URL, a
# matéria aberta é resolvida via WebSocket (get_materia_aberta/
# get_materia_expediente_aberta) — não mais pela tela legada nominal.html/
# VotacaoNominalAbstract/VotacaoNominalView/VotacaoNominalExpedienteView,
# removida nesta unificação. bloquear-registro-votacao/reabrir-votacao,
# que só existiam lá, viraram _toggle_registro() (sapl/painel/views.py),
# testado abaixo. votacaonominaledit/votacaonominalexpedit (edição de um
# registro já fechado) usam uma base diferente (VotacaoNominalEditAbstract)
# e continuam intocados.


@pytest.mark.django_db(transaction=False)
def test_toggle_registro_bloqueia_e_reabre_sem_mexer_em_votos():
    """
    Regressão do que test_bloquear_e_reabrir_votacao_nao_mexe_em_votos_
    existentes (tela legada) cobria: bloquear/reabrir o registro não pode
    alterar nenhum voto já registrado, só a flag que trava votos novos.
    """
    sessao, ordem = _ordem_nominal_aberta()
    votante = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=votante, voto='Sim')
    user = baker.make(get_user_model())

    result = _toggle_registro(user, sessao.pk, True)
    ordem.refresh_from_db()
    assert ordem.registro_aberto is True
    assert result == {"registro_aberto": True}

    result2 = _toggle_registro(user, sessao.pk, False)
    ordem.refresh_from_db()
    assert ordem.registro_aberto is False
    assert result2 == {"registro_aberto": False}

    voto = VotoParlamentar.objects.get(ordem=ordem, parlamentar=votante)
    assert voto.voto == 'Sim'


@pytest.mark.django_db(transaction=False)
def test_toggle_registro_falha_sem_materia_nominal_aberta():
    sessao = _sessao_plenaria()
    user = baker.make(get_user_model())
    with pytest.raises(VoteError):
        _toggle_registro(user, sessao.pk, True)


@pytest.mark.django_db(transaction=False)
def test_abrir_votacao_ja_aberta_e_idempotente(admin_client):
    """
    Regressão: clicar em "Abrir Votação" para uma matéria que já está aberta
    (ex.: duplo clique, ou a lista ainda não recarregou para trocar o botão
    por "Registrar Votação") caía em verifica_votacoes_abertas(), que trata
    a própria matéria como uma "outra" votação conflitante — mostra a
    mensagem "existem votações abertas... foram fechadas" e fecha a matéria
    (para reabri-la em seguida, já que o código sempre prossegue). O
    resultado final até ficava certo (votacao_aberta=True), mas a mensagem
    era enganosa. Reabrir a própria matéria já aberta precisa ser
    silenciosamente idempotente.
    """
    sessao, ordem = _ordem_nominal_aberta()
    sessao.iniciada = True
    sessao.finalizada = False
    sessao.save()
    _presente(sessao)

    url = reverse('sapl.sessao:abrir_votacao', kwargs={'pk': ordem.pk, 'spk': sessao.pk})
    url += '?tipo_materia=ordem'

    response = admin_client.get(url, follow=True)

    assert response.status_code == 200
    ordem.refresh_from_db()
    assert ordem.votacao_aberta is True

    mensagens = [str(m) for m in response.context['messages']]
    assert not any('foram fechadas' in m for m in mensagens)


def _abrir_votacao_url(sessao, ordem):
    return reverse('sapl.sessao:abrir_votacao',
                   kwargs={'pk': ordem.pk, 'spk': sessao.pk}) + '?tipo_materia=ordem'


@pytest.mark.django_db(transaction=False)
def test_abrir_outra_votacao_zera_bloqueio_da_anterior(admin_client):
    """
    Abrir Y sem encerrar X fecha X; X não pode voltar com os tablets
    bloqueados (registro_aberto=True) quando for reaberta.
    """
    sessao, x = _ordem_nominal_aberta()
    sessao.iniciada = True
    sessao.finalizada = False
    sessao.save()
    _presente(sessao)
    x.registro_aberto = True
    x.save()
    y = baker.make(OrdemDia, sessao_plenaria=sessao, materia=_materia(),
                   tipo_votacao=NOMINAL, votacao_aberta=False)

    admin_client.get(_abrir_votacao_url(sessao, y))

    x.refresh_from_db()
    y.refresh_from_db()
    assert y.votacao_aberta is True
    assert x.votacao_aberta is False
    assert x.registro_aberto is False

    # Legado: matéria fechada que ficou com registro_aberto=True.
    OrdemDia.objects.filter(pk=x.pk).update(registro_aberto=True)
    admin_client.get(_abrir_votacao_url(sessao, x))

    x.refresh_from_db()
    assert x.votacao_aberta is True
    assert x.registro_aberto is False


@pytest.mark.django_db(transaction=False)
def test_abrir_votacao_concorrente_mostra_erro_em_vez_de_500(admin_client):
    """
    O lock de abrir_votacao() é por sessão, mas a unicidade de
    votacao_aberta é global: uma abertura simultânea em outra sessão faz o
    save cair no índice parcial. O fechamento das outras votações é
    desfeito junto, então a mensagem "foram fechadas" não pode aparecer.
    """
    sessao, ordem = _ordem_nominal_aberta()
    ordem.votacao_aberta = False
    ordem.save()
    _, outra = _ordem_nominal_aberta()
    sessao.iniciada = True
    sessao.finalizada = False
    sessao.save()
    _presente(sessao)

    with mock.patch.object(OrdemDia, 'save', side_effect=IntegrityError):
        response = admin_client.get(_abrir_votacao_url(sessao, ordem), follow=True)

    assert response.status_code == 200
    ordem.refresh_from_db()
    outra.refresh_from_db()
    assert ordem.votacao_aberta is False
    assert outra.votacao_aberta is True
    mensagens = [str(m) for m in response.context['messages']]
    assert any('aberta simultaneamente' in m for m in mensagens)
    assert not any('foram fechadas' in m for m in mensagens)


@pytest.mark.django_db(transaction=False)
def test_abrir_votacao_avisa_que_fechou_as_outras(admin_client):
    sessao, ordem = _ordem_nominal_aberta()
    ordem.votacao_aberta = False
    ordem.save()
    _, outra = _ordem_nominal_aberta()
    sessao.iniciada = True
    sessao.finalizada = False
    sessao.save()
    _presente(sessao)

    response = admin_client.get(_abrir_votacao_url(sessao, ordem), follow=True)

    outra.refresh_from_db()
    assert outra.votacao_aberta is False
    mensagens = [str(m) for m in response.context['messages']]
    assert any('foram fechadas' in m for m in mensagens)


@pytest.mark.django_db(transaction=False)
def test_unique_constraint_impede_voto_duplicado(admin_client):
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=parlamentar, voto='Sim')

    with pytest.raises(IntegrityError):
        VotoParlamentar.objects.create(
            ordem=ordem, parlamentar=parlamentar, voto='Não')


@pytest.mark.django_db(transaction=False)
def test_unique_constraint_impede_duas_ordens_abertas():
    sessao, ordem = _ordem_nominal_aberta()
    outra = baker.make(OrdemDia, sessao_plenaria=sessao, materia=ordem.materia,
                       tipo_votacao=NOMINAL, votacao_aberta=False)

    with pytest.raises(IntegrityError):
        outra.votacao_aberta = True
        outra.save()


@pytest.mark.django_db(transaction=False)
def test_migracao_0071_remove_votos_duplicados_antes_da_constraint():
    import importlib

    from django.apps import apps as real_apps
    from django.db import connection

    migracao = importlib.import_module(
        'sapl.sessao.migrations.0071_votoparlamentar_unique_constraint')

    with connection.cursor() as cursor:
        cursor.execute(
            'DROP INDEX sessao_votoparlamentar_unique_parlamentar_ordem')

    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    antigo = baker.make(VotoParlamentar, ordem=ordem,
                        parlamentar=parlamentar, voto='Não')
    recente = baker.make(VotoParlamentar, ordem=ordem,
                         parlamentar=parlamentar, voto='Sim')

    migracao.remove_votos_duplicados(real_apps, None)

    votos = VotoParlamentar.objects.filter(
        ordem=ordem, parlamentar=parlamentar)
    assert list(votos.values_list('id', flat=True)) == [recente.id]
    assert not votos.filter(id=antigo.id).exists()


@pytest.mark.django_db(transaction=False)
def test_migracao_0072_fecha_duplicatas_antes_da_constraint():
    """
    A função de dados da migration 0072 precisa fechar duplicatas
    pré-existentes antes do AddConstraint — senão a migration falharia ao
    ser aplicada num banco com dado antigo (de antes desta invariante
    existir). Testa a função isoladamente: como o teste roda dentro de uma
    transação que é desfeita no final, é seguro derrubar o índice aqui
    (DDL é transacional no Postgres).
    """
    import importlib

    from django.apps import apps as real_apps
    from django.db import connection

    migracao = importlib.import_module(
        'sapl.sessao.migrations.0072_votacao_aberta_unique_constraint')

    with connection.cursor() as cursor:
        cursor.execute('DROP INDEX sessao_ordemdia_unique_votacao_aberta')

    sessao, mais_antiga = _ordem_nominal_aberta()
    mais_recente = baker.make(OrdemDia, sessao_plenaria=sessao,
                              materia=mais_antiga.materia, tipo_votacao=NOMINAL,
                              votacao_aberta=True, registro_aberto=True)
    assert mais_recente.pk > mais_antiga.pk
    # Legado: o GET antigo da tela de registro deixava registro_aberto=True
    # em matérias já encerradas.
    encerrada = baker.make(OrdemDia, sessao_plenaria=sessao,
                           materia=mais_antiga.materia, tipo_votacao=NOMINAL,
                           votacao_aberta=False, registro_aberto=True)

    migracao.fecha_materias_abertas_duplicadas(real_apps, None)

    mais_antiga.refresh_from_db()
    mais_recente.refresh_from_db()
    encerrada.refresh_from_db()
    assert mais_antiga.votacao_aberta is False
    assert mais_recente.votacao_aberta is True
    assert mais_recente.registro_aberto is False
    assert encerrada.registro_aberto is False


@pytest.mark.django_db(transaction=False)
def test_api_nao_permite_abrir_votacao_via_patch(admin_client):
    """
    Regressão do bypass encontrado na auditoria: a API auto-gerada
    (drfautoapi) não pode mais aceitar votacao_aberta/registro_aberto —
    senão qualquer "Operador de Sessão Plenária" conseguiria abrir uma
    matéria via PATCH direto, pulando verifica_votacoes_abertas() e o
    lock em abrir_votacao().
    """
    sessao, ordem = _ordem_nominal_aberta()
    ordem.votacao_aberta = False
    ordem.save()

    url = '/api/sessao/ordemdia/{}/'.format(ordem.pk)
    response = admin_client.patch(
        url, data={'votacao_aberta': True}, content_type='application/json')

    assert response.status_code in (200, 202)
    ordem.refresh_from_db()
    assert ordem.votacao_aberta is False


# Regras do #3855 aplicadas ao fluxo v2 (close_voting / _cast_vote /
# votante_view), que substituiu VotacaoNominalAbstract.

def _close_voting(client, sessao, tipo_resultado):
    return client.post(
        reverse('sapl.painel:close_voting', kwargs={'controller_id': sessao.pk}),
        {'resultado_id': tipo_resultado.pk, 'observacoes': ''})


@pytest.mark.django_db(transaction=False)
def test_close_voting_conta_so_presentes_e_apaga_voto_de_quem_saiu(admin_client):
    sessao, ordem = _ordem_nominal_aberta()
    presente = _presente(sessao)
    saiu = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=presente, voto='Não')
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=saiu, voto='Sim')
    PresencaOrdemDia.objects.filter(sessao_plenaria=sessao, parlamentar=saiu).delete()
    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Rejeitada', natureza='R')

    response = _close_voting(admin_client, sessao, tipo_resultado)

    assert response.status_code == 200
    registro = RegistroVotacao.objects.get(ordem=ordem)
    assert registro.numero_votos_sim == 0
    assert registro.numero_votos_nao == 1
    assert not VotoParlamentar.objects.filter(ordem=ordem, parlamentar=saiu).exists()


@pytest.mark.django_db(transaction=False)
def test_close_voting_registra_nao_votou_para_presentes_sem_voto(admin_client):
    sessao, ordem = _ordem_nominal_aberta()
    votou = _presente(sessao)
    nao_votou = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=votou, voto='Sim')
    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Aprovada', natureza='A')

    response = _close_voting(admin_client, sessao, tipo_resultado)

    assert response.status_code == 200
    registro = RegistroVotacao.objects.get(ordem=ordem)
    voto = VotoParlamentar.objects.get(ordem=ordem, parlamentar=nao_votou)
    assert voto.voto == 'Não Votou'
    assert voto.votacao_id == registro.id


@pytest.mark.django_db(transaction=False)
def test_close_voting_sem_votos_nao_grava_nao_votou(admin_client):
    """O operador precisa poder corrigir e tentar de novo."""
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Aprovada', natureza='A')

    response = _close_voting(admin_client, sessao, tipo_resultado)

    assert response.status_code == 400
    assert not VotoParlamentar.objects.filter(ordem=ordem, parlamentar=parlamentar).exists()
    ordem.refresh_from_db()
    assert ordem.votacao_aberta is True


@pytest.mark.django_db(transaction=False)
def test_close_voting_preserva_autoria_e_zera_bloqueio(admin_client):
    sessao, ordem = _ordem_nominal_aberta()
    ordem.registro_aberto = True
    ordem.save()
    parlamentar = _presente(sessao)
    autor = baker.make(get_user_model())
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=parlamentar, voto='Sim',
               user=autor, ip='10.0.0.1', votado_pelo_parlamentar=True)
    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Aprovada', natureza='A')

    response = _close_voting(admin_client, sessao, tipo_resultado)

    assert response.status_code == 200
    voto = VotoParlamentar.objects.get(ordem=ordem, parlamentar=parlamentar)
    assert voto.user_id == autor.pk
    assert voto.ip == '10.0.0.1'
    ordem.refresh_from_db()
    assert ordem.votacao_aberta is False
    assert ordem.registro_aberto is False


@pytest.mark.django_db(transaction=False)
def test_operador_nao_sobrescreve_voto_do_parlamentar():
    """O voto registrado pelo próprio parlamentar (tablet) prevalece."""
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=parlamentar, voto='Sim',
               votado_pelo_parlamentar=True)
    operador = baker.make(get_user_model())

    with pytest.raises(VoteError):
        _cast_vote(operador, sessao.pk, parlamentar.pk, 'Não', ip='127.0.0.1')

    voto = VotoParlamentar.objects.get(ordem=ordem, parlamentar=parlamentar)
    assert voto.voto == 'Sim'
    assert voto.votado_pelo_parlamentar is True


@pytest.mark.django_db(transaction=False)
def test_operador_pode_corrigir_voto_que_ele_mesmo_registrou():
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    operador = baker.make(get_user_model())

    _cast_vote(operador, sessao.pk, parlamentar.pk, 'Sim', ip='127.0.0.1')
    _cast_vote(operador, sessao.pk, parlamentar.pk, 'Não', ip='127.0.0.1')

    voto = VotoParlamentar.objects.get(ordem=ordem, parlamentar=parlamentar)
    assert voto.voto == 'Não'
    assert voto.votado_pelo_parlamentar is False


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('cenario', ['ausente', 'bloqueado'])
def test_operador_nao_registra_voto_invalido(cenario):
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    if cenario == 'ausente':
        PresencaOrdemDia.objects.filter(sessao_plenaria=sessao).delete()
    else:
        ordem.registro_aberto = True
        ordem.save()
    operador = baker.make(get_user_model())

    with pytest.raises(VoteError):
        _cast_vote(operador, sessao.pk, parlamentar.pk, 'Sim', ip='127.0.0.1')

    assert not VotoParlamentar.objects.filter(ordem=ordem, parlamentar=parlamentar).exists()


@pytest.mark.django_db(transaction=False)
def test_operador_nao_votou_desfaz_o_proprio_lancamento_sem_gravar_linha():
    """
    'Não Votou' no <select> da Mesa desfaz o lançamento do operador; a
    linha 'Não Votou' só é criada no encerramento.
    """
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    operador = baker.make(get_user_model())

    _cast_vote(operador, sessao.pk, parlamentar.pk, 'Não Votou', ip='127.0.0.1')
    assert not VotoParlamentar.objects.filter(ordem=ordem, parlamentar=parlamentar).exists()

    _cast_vote(operador, sessao.pk, parlamentar.pk, 'Sim', ip='127.0.0.1')
    _cast_vote(operador, sessao.pk, parlamentar.pk, 'Não Votou', ip='127.0.0.1')
    assert not VotoParlamentar.objects.filter(ordem=ordem, parlamentar=parlamentar).exists()


@pytest.mark.django_db(transaction=False)
def test_operador_nao_desfaz_voto_do_parlamentar():
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=parlamentar, voto='Sim',
               votado_pelo_parlamentar=True)
    operador = baker.make(get_user_model())

    with pytest.raises(VoteError):
        _cast_vote(operador, sessao.pk, parlamentar.pk, 'Não Votou', ip='127.0.0.1')

    assert VotoParlamentar.objects.get(ordem=ordem, parlamentar=parlamentar).voto == 'Sim'


@pytest.mark.django_db(transaction=False)
def test_toggle_registro_nao_regrava_outros_campos():
    sessao, ordem = _ordem_nominal_aberta()
    user = baker.make(get_user_model())
    # Outra operação altera a matéria depois que _toggle_registro a leu.
    original = _toggle_registro.__globals__['get_materia_aberta']

    def get_materia_aberta_obsoleta(pk):
        materia = original(pk)
        OrdemDia.objects.filter(pk=materia.pk).update(resultado='Aprovada')
        return materia

    with mock.patch.dict(_toggle_registro.__globals__,
                         {'get_materia_aberta': get_materia_aberta_obsoleta}):
        _toggle_registro(user, sessao.pk, True)

    ordem.refresh_from_db()
    assert ordem.registro_aberto is True
    assert ordem.resultado == 'Aprovada'
