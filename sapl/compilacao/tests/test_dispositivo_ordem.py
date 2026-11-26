import itertools
from unittest import mock

import pytest
from model_bakery import baker

from sapl.compilacao.models import (Dispositivo, TextoArticulado,
                                    TipoDispositivo)


@pytest.fixture
def texto():
    ta = baker.make(TextoArticulado)
    tipo = baker.make(TipoDispositivo, contagem_continua=False)
    return ta, tipo


_numeracao = itertools.count(1)


def _dispositivo(ta, tipo, ordem, nivel=0):
    return baker.make(
        Dispositivo, ta=ta, tipo_dispositivo=tipo, ordem=ordem, nivel=nivel,
        dispositivo0=next(_numeracao), dispositivo_pai=None)


def _ordens(ta):
    return list(Dispositivo.objects.filter(
        ta=ta).order_by('ordem').values_list('ordem', flat=True))


@pytest.mark.django_db(transaction=False)
def test_criar_espaco_usa_lacuna_sem_deslocar(texto):
    ta, tipo = texto
    d1 = _dispositivo(ta, tipo, 1000)
    _dispositivo(ta, tipo, 2000)
    _dispositivo(ta, tipo, 3000)

    for local in ('json_add_next', 'json_add_in', 'json_add_in_with_auto'):
        assert d1.criar_espaco(espaco_a_criar=1, local=local) == 1500
        assert _ordens(ta) == [1000, 2000, 3000]


@pytest.mark.django_db(transaction=False)
def test_criar_espaco_antes_do_primeiro_usa_lacuna(texto):
    ta, tipo = texto
    d1 = _dispositivo(ta, tipo, 1000)
    _dispositivo(ta, tipo, 2000)

    assert d1.criar_espaco(espaco_a_criar=1) == 500
    assert _ordens(ta) == [1000, 2000]


@pytest.mark.django_db(transaction=False)
def test_criar_espaco_sem_lacuna_desloca_os_seguintes(texto):
    ta, tipo = texto
    d1 = _dispositivo(ta, tipo, 1000)
    _dispositivo(ta, tipo, 1001)
    _dispositivo(ta, tipo, 2000)

    assert d1.criar_espaco(espaco_a_criar=1, local='json_add_next') == 1001
    assert _ordens(ta) == [1000, 2001, 3000]


@pytest.mark.django_db(transaction=False)
def test_criar_espaco_para_varios_desloca_os_seguintes(texto):
    ta, tipo = texto
    d1 = _dispositivo(ta, tipo, 1000)
    _dispositivo(ta, tipo, 2000)
    _dispositivo(ta, tipo, 3000)

    assert d1.criar_espaco(espaco_a_criar=2, local='json_add_next') == 2000
    assert _ordens(ta) == [1000, 4000, 5000]


@pytest.mark.django_db(transaction=False)
def test_criar_espaco_no_fim_do_texto(texto):
    ta, tipo = texto
    _dispositivo(ta, tipo, 1000)
    d2 = _dispositivo(ta, tipo, 2000)

    assert d2.criar_espaco(espaco_a_criar=1, local='json_add_next') == 3000
    assert _ordens(ta) == [1000, 2000]


@pytest.mark.django_db(transaction=False)
def test_criar_espaco_insercoes_repetidas_no_mesmo_ponto(texto):
    """Esgota a lacuna entre dois dispositivos e confere que, depois disso,
    o deslocamento continua mantendo a ordem e a unicidade."""
    ta, tipo = texto
    d1 = _dispositivo(ta, tipo, 1000)
    d2 = _dispositivo(ta, tipo, 2000)
    d3 = _dispositivo(ta, tipo, 3000)

    novos = []
    for i in range(15):
        d2.refresh_from_db()
        ordem = d2.criar_espaco(espaco_a_criar=1)
        novos.append(_dispositivo(ta, tipo, ordem))

    esperado = [d1.pk] + [n.pk for n in novos] + [d2.pk, d3.pk]
    assert list(Dispositivo.objects.filter(ta=ta).order_by(
        'ordem').values_list('pk', flat=True)) == esperado
    assert len(set(_ordens(ta))) == len(esperado)


@pytest.mark.django_db(transaction=False)
def test_save_chama_clean_so_quando_pedido(texto):
    ta, tipo = texto
    d1 = _dispositivo(ta, tipo, 1000)

    with mock.patch.object(Dispositivo, 'clean') as clean:
        d1.save()
        assert clean.call_count == 1
        d1.save(clean=False)
        assert clean.call_count == 1
