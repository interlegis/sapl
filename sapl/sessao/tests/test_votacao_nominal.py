import re
from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.db import IntegrityError
from django.urls import reverse
from model_bakery import baker

from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
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


def _registrar_url(sessao, ordem):
    return reverse('sapl.sessao:votacaonominal',
                   kwargs={'pk': sessao.pk, 'oid': ordem.pk, 'mid': ordem.materia_id})


@pytest.mark.django_db(transaction=False)
def test_get_registrar_votacao_nao_bloqueia_novos_votos(admin_client):
    """
    Regressão da causa raiz #1: abrir a tela "Registrar Votação" não pode,
    sozinho, impedir que vereadores que ainda não votaram continuem votando.
    """
    sessao, ordem = _ordem_nominal_aberta()
    _presente(sessao)

    response = admin_client.get(_registrar_url(sessao, ordem))

    assert response.status_code == 200
    ordem.refresh_from_db()
    assert ordem.registro_aberto is False


@pytest.mark.django_db(transaction=False)
def test_post_sem_acao_reconhecida_redireciona_para_registro(admin_client):
    sessao, ordem = _ordem_nominal_aberta()
    _presente(sessao)

    response = admin_client.post(_registrar_url(sessao, ordem) + '?page=2', {})

    assert response.status_code == 302
    assert response.url == _registrar_url(sessao, ordem) + '?page=2'
    ordem.refresh_from_db()
    assert ordem.registro_aberto is False


@pytest.mark.django_db(transaction=False)
def test_botao_registrar_votacao_nominal_usa_get(admin_client):
    """
    A tela de registro não tem efeito colateral no GET; com o botão em GET
    o ?page vai na URL e é preservado até o redirect final do post().
    """
    sessao, ordem = _ordem_nominal_aberta()

    response = admin_client.get(
        reverse('sapl.sessao:ordemdia_list', kwargs={'pk': sessao.pk}))

    conteudo = response.content.decode()
    form = re.search(
        r'<form action="%s"[^>]*>' % re.escape(_registrar_url(sessao, ordem)),
        conteudo)
    assert form
    assert form.group(0) == '<form action="%s">' % _registrar_url(sessao, ordem)


@pytest.mark.django_db(transaction=False)
def test_bloquear_e_reabrir_votacao_nao_mexe_em_votos_existentes(admin_client):
    sessao, ordem = _ordem_nominal_aberta()
    votante = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=votante, voto='Sim')

    url = _registrar_url(sessao, ordem)

    response = admin_client.post(url, {'bloquear-registro-votacao': '1'})
    assert response.status_code == 302
    ordem.refresh_from_db()
    assert ordem.registro_aberto is True

    response = admin_client.post(url, {'reabrir-votacao': '1'})
    assert response.status_code == 302
    ordem.refresh_from_db()
    assert ordem.registro_aberto is False

    voto = VotoParlamentar.objects.get(ordem=ordem, parlamentar=votante)
    assert voto.voto == 'Sim'


@pytest.mark.django_db(transaction=False)
def test_salvar_votacao_nao_sobrescreve_voto_ja_registrado(admin_client):
    """
    Regressão do modelo de concorrência (3b): um formulário de "Fechar
    Votação" com um valor obsoleto para quem já votou pelo tablet não pode
    sobrescrever esse voto — só preenche quem ainda não tem voto registrado.
    """
    sessao, ordem = _ordem_nominal_aberta()
    ja_votou = _presente(sessao)
    ainda_nao_votou = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=ja_votou, voto='Sim')

    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Aprovada', natureza='A')

    url = _registrar_url(sessao, ordem)
    payload = {
        'salvar-votacao': '1',
        'resultado_votacao': str(tipo_resultado.pk),
        'observacao': '',
        'voto_parlamentar': [
            # valor obsoleto: a tela do operador ainda não sabia que este
            # parlamentar já havia votado "Sim" pelo tablet
            'Não Votou:{}'.format(ja_votou.pk),
            'Não:{}'.format(ainda_nao_votou.pk),
        ],
    }

    response = admin_client.post(url, payload)
    assert response.status_code == 302

    voto_ja_votou = VotoParlamentar.objects.get(ordem=ordem, parlamentar=ja_votou)
    assert voto_ja_votou.voto == 'Sim'

    voto_novo = VotoParlamentar.objects.get(ordem=ordem, parlamentar=ainda_nao_votou)
    assert voto_novo.voto == 'Não'

    registro = RegistroVotacao.objects.get(ordem=ordem)
    assert registro.numero_votos_sim == 1
    assert registro.numero_votos_nao == 1

    ordem.refresh_from_db()
    assert ordem.votacao_aberta is False
    assert ordem.registro_aberto is False

    # O 'Não Votou' enviado para quem já votou é só o valor padrão do
    # <select>, não um conflito — não pode gerar o aviso de não sobrescrito.
    avisos = [str(m) for m in get_messages(response.wsgi_request)]
    assert not any('não foram sobrescritos' in a for a in avisos)


@pytest.mark.django_db(transaction=False)
def test_salvar_votacao_avisa_quando_voto_do_tablet_diverge_do_formulario(admin_client):
    sessao, ordem = _ordem_nominal_aberta()
    ja_votou = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=ja_votou, voto='Sim')
    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Aprovada', natureza='A')

    response = admin_client.post(_registrar_url(sessao, ordem), {
        'salvar-votacao': '1',
        'resultado_votacao': str(tipo_resultado.pk),
        'observacao': '',
        'voto_parlamentar': ['Não:{}'.format(ja_votou.pk)],
    })

    assert response.status_code == 302
    assert VotoParlamentar.objects.get(ordem=ordem, parlamentar=ja_votou).voto == 'Sim'
    avisos = [str(m) for m in get_messages(response.wsgi_request)]
    assert any('não foram sobrescritos' in a for a in avisos)


@pytest.mark.django_db(transaction=False)
def test_salvar_votacao_registra_nao_votou_para_presentes_sem_voto(admin_client):
    """
    Relatórios, transparência e o painel leem VotoParlamentar por votação:
    quem estava presente e não votou precisa ficar registrado como
    'Não Votou', vinculado ao RegistroVotacao.
    """
    sessao, ordem = _ordem_nominal_aberta()
    votou = _presente(sessao)
    nao_votou = _presente(sessao)
    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Aprovada', natureza='A')

    response = admin_client.post(_registrar_url(sessao, ordem), {
        'salvar-votacao': '1',
        'resultado_votacao': str(tipo_resultado.pk),
        'observacao': '',
        'voto_parlamentar': [
            'Sim:{}'.format(votou.pk),
            'Não Votou:{}'.format(nao_votou.pk),
        ],
    })

    assert response.status_code == 302
    registro = RegistroVotacao.objects.get(ordem=ordem)
    assert registro.numero_votos_sim == 1
    voto = VotoParlamentar.objects.get(ordem=ordem, parlamentar=nao_votou)
    assert voto.voto == 'Não Votou'
    assert voto.votacao_id == registro.id


@pytest.mark.django_db(transaction=False)
def test_salvar_votacao_ignora_voto_de_quem_teve_presenca_removida(admin_client):
    """
    Parlamentar vota pelo tablet, sai e tem a presença removida antes do
    encerramento: o voto não entra na contagem e é apagado.
    """
    sessao, ordem = _ordem_nominal_aberta()
    presente = _presente(sessao)
    saiu = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=saiu, voto='Sim')
    PresencaOrdemDia.objects.filter(sessao_plenaria=sessao, parlamentar=saiu).delete()
    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Rejeitada', natureza='R')

    response = admin_client.post(_registrar_url(sessao, ordem), {
        'salvar-votacao': '1',
        'resultado_votacao': str(tipo_resultado.pk),
        'observacao': '',
        'voto_parlamentar': ['Não:{}'.format(presente.pk)],
    })

    assert response.status_code == 302
    registro = RegistroVotacao.objects.get(ordem=ordem)
    assert registro.numero_votos_sim == 0
    assert registro.numero_votos_nao == 1
    assert not VotoParlamentar.objects.filter(ordem=ordem, parlamentar=saiu).exists()


@pytest.mark.django_db(transaction=False)
def test_salvar_votacao_sem_votos_nao_trava_selects_para_nova_tentativa(admin_client):
    """
    Regressão: fechar a votação sem nenhum voto real corretamente mostra um
    erro, mas antes disso o laço de salvamento em lote criava um
    VotoParlamentar com voto='Não Votou' para cada parlamentar cujo select
    não foi tocado (o valor padrão do <select>). Esses registros persistiam
    mesmo com o fechamento falhando (o bloco atomic não é revertido, já que
    form_invalid retorna normalmente em vez de lançar), e nominal.html
    desabilita o <select> de qualquer parlamentar com um VotoParlamentar
    existente — travando o operador para sempre sem conseguir registrar
    nenhum voto para essa matéria.
    """
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Aprovada', natureza='A')

    url = _registrar_url(sessao, ordem)
    payload = {
        'salvar-votacao': '1',
        'resultado_votacao': str(tipo_resultado.pk),
        'observacao': '',
        'voto_parlamentar': ['Não Votou:{}'.format(parlamentar.pk)],
    }

    response = admin_client.post(url, payload)
    assert response.status_code == 302

    assert not VotoParlamentar.objects.filter(
        ordem=ordem, parlamentar=parlamentar).exists()

    ordem.refresh_from_db()
    assert ordem.votacao_aberta is True

    # O operador consegue tentar de novo, agora com um voto real.
    response2 = admin_client.post(url, {
        'salvar-votacao': '1',
        'resultado_votacao': str(tipo_resultado.pk),
        'observacao': '',
        'voto_parlamentar': ['Sim:{}'.format(parlamentar.pk)],
    })
    assert response2.status_code == 302
    ordem.refresh_from_db()
    assert ordem.votacao_aberta is False
    assert VotoParlamentar.objects.get(ordem=ordem, parlamentar=parlamentar).voto == 'Sim'


@pytest.mark.django_db(transaction=False)
def test_status_da_votacao_reflete_troca_de_voto_do_parlamentar(admin_client):
    """
    Regressão: a tela de registro (nominal.html) não atualizava a linha de
    um parlamentar que trocou o voto durante a janela de votação — o poll
    antigo só marcava "já votou" uma vez e nunca revisitava o valor. O poll
    (?status=1) precisa sempre devolver o voto atual, não só se existe.
    """
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    voto = baker.make(VotoParlamentar, ordem=ordem, parlamentar=parlamentar,
                      voto='Sim')

    url = _registrar_url(sessao, ordem) + '?status=1'
    response = admin_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data['votos'] == {str(parlamentar.pk): 'Sim'}
    assert data['votacao_aberta'] is True
    assert data['registro_aberto'] is False
    assert data['ja_registrada'] is False

    voto.voto = 'Não'
    voto.save()

    response2 = admin_client.get(url)
    assert response2.json()['votos'] == {str(parlamentar.pk): 'Não'}


@pytest.mark.django_db(transaction=False)
def test_status_da_votacao_nao_depende_de_mostrar_voto(admin_client):
    """
    O poll da tela de registro é só para a Mesa, não para o público — ao
    contrário de sapl.painel:dados_painel, ele não pode mascarar o valor
    real do voto por trás de "Voto Informado" mesmo quando a Casa configura
    mostrar_voto=False (essa config controla o telão público, não a tela de
    registro da própria Mesa). Como o endpoint nem consulta essa
    configuração, isso é garantido por construção — este teste só
    documenta a expectativa.
    """
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    baker.make(VotoParlamentar, ordem=ordem, parlamentar=parlamentar,
               voto='Abstenção')

    url = _registrar_url(sessao, ordem) + '?status=1'
    data = admin_client.get(url).json()
    assert data['votos'][str(parlamentar.pk)] == 'Abstenção'


@pytest.mark.django_db(transaction=False)
def test_status_da_votacao_nao_redireciona_apos_encerrar_votacao(
        admin_client):
    """
    _get_materia_votacao (usado pelo GET normal) redireciona com uma
    mensagem quando a matéria já foi votada — comportamento certo para
    navegação, errado para um poll em background. O branch ?status=1 não
    pode herdar esse redirect.
    """
    sessao, ordem = _ordem_nominal_aberta()
    parlamentar = _presente(sessao)
    tipo_resultado = baker.make(TipoResultadoVotacao, nome='Aprovada',
                                natureza='A')

    url = _registrar_url(sessao, ordem)
    admin_client.post(url, {
        'salvar-votacao': '1',
        'resultado_votacao': str(tipo_resultado.pk),
        'observacao': '',
        'voto_parlamentar': ['Sim:{}'.format(parlamentar.pk)],
    })

    response = admin_client.get(url + '?status=1')
    assert response.status_code == 200
    data = response.json()
    assert data['ja_registrada'] is True
    assert data['votacao_aberta'] is False


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
