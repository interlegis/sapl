import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from model_bakery import baker

from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.painel.views import VoteError, _toggle_registro
from sapl.parlamentares.models import (Legislatura, Parlamentar,
                                       SessaoLegislativa)
from sapl.sessao.models import (OrdemDia, PresencaOrdemDia, RegistroVotacao,
                                SessaoPlenaria, TipoResultadoVotacao,
                                TipoSessaoPlenaria, VotoParlamentar)

NOMINAL = 2


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
def test_migracao_0071_fecha_duplicatas_antes_da_constraint():
    """
    A função de dados da migration 0071 precisa fechar duplicatas
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
        'sapl.sessao.migrations.0071_votacao_aberta_unique_constraint')

    with connection.cursor() as cursor:
        cursor.execute('DROP INDEX sessao_ordemdia_unique_votacao_aberta')

    sessao, mais_antiga = _ordem_nominal_aberta()
    mais_recente = baker.make(OrdemDia, sessao_plenaria=sessao,
                              materia=mais_antiga.materia, tipo_votacao=NOMINAL,
                              votacao_aberta=True)
    assert mais_recente.pk > mais_antiga.pk

    migracao.fecha_matérias_abertas_duplicadas(real_apps, None)

    mais_antiga.refresh_from_db()
    mais_recente.refresh_from_db()
    assert mais_antiga.votacao_aberta is False
    assert mais_recente.votacao_aberta is True


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
