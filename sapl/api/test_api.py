from model_bakery import baker
import pytest

from sapl.parlamentares.models import Legislatura, ComposicaoMesa, Parlamentar,\
 SessaoLegislativa, CargoMesa

@pytest.mark.django_db(transaction=False)
def test_get_mesa_diretora():
    #criar legislatura, sessao e parlamentares
    parlamentar = baker.make(Parlamentar, nome_parlamentar='Joseph Joestar', id=8)

    legislatura = baker.make(Legislatura, id=34)

    sessao = baker.make(SessaoLegislativa, legislatura=legislatura)

    cargo = baker.make(CargoMesa, descricao="presidente")

    #passar informações para a composicao_mesa
    mesa = baker.make(ComposicaoMesa, parlamentar=parlamentar,
    sessao_legislativa=sessao, cargo=cargo)

    print(mesa.cargo)

    #checagens  