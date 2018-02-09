from datetime import datetime

import pytest
from model_mommy import mommy
from sapl.parlamentares.models import Filiacao, Legislatura, Mandato

pytestmark = pytest.mark.django_db


def data(valor):
    return datetime.strptime(valor, '%Y-%m-%d').date()


def test_filiacoes():
    legislatura = mommy.make(Legislatura,
                             data_inicio=data('2001-01-01'),
                             data_fim=data('2001-12-31'),
                             )
    mandato = mommy.make(Mandato, legislatura=legislatura)
    f1_fora, f2, f3, f4 = [mommy.make(Filiacao,
                                      parlamentar=mandato.parlamentar,
                                      data=ini,
                                      data_desfiliacao=fim)
                           for ini, fim in (
        (data('2000-01-01'), data('2000-12-31')),
        (data('2000-01-01'), data('2001-03-01')),
        (data('2001-03-02'), data('2001-10-01')),
        (data('2001-10-02'), None),
    )]
    assert mandato.get_partidos() == [f2.partido.sigla,
                                      f3.partido.sigla,
                                      f4.partido.sigla]
