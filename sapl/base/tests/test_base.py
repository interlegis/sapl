import pytest
from model_mommy import mommy

from sapl.base.models import CasaLegislativa


@pytest.mark.django_db(transaction=False)
def test_casa_legislativa_model():
    mommy.make(CasaLegislativa,
               nome='Teste_Nome_Casa_Legislativa',
               sigla='TSCL',
               endereco='Teste_Endereço_Casa_Legislativa',
               cep='12345678',
               municipio='Teste_Municipio_Casa_Legislativa',
               uf='DF')

    casa_legislativa = CasaLegislativa.objects.first()

    assert casa_legislativa.nome == 'Teste_Nome_Casa_Legislativa'
    assert casa_legislativa.sigla == 'TSCL'
    assert casa_legislativa.endereco == 'Teste_Endereço_Casa_Legislativa'
    assert casa_legislativa.cep == '12345678'
    assert casa_legislativa.municipio == 'Teste_Municipio_Casa_Legislativa'
    assert casa_legislativa.uf == 'DF'
