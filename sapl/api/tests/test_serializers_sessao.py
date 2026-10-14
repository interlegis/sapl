import pytest
from model_bakery import baker

from sapl.api.serializers import SessaoPlenariaECidadaniaSerializer
from sapl.base.models import CasaLegislativa
from sapl.sessao.models import SessaoPlenaria


@pytest.mark.django_db(transaction=False)
def test_sessao_ecidadania_serializa_dados_da_casa():
    casa = baker.make(CasaLegislativa, nome='Câmara Municipal', sigla='CM',
                      endereco='Praça Central')
    sessao = baker.make(SessaoPlenaria)

    data = SessaoPlenariaECidadaniaSerializer(sessao).data

    assert data['txtNomeOrgao'] == casa.nome
    assert data['txtSiglaOrgao'] == casa.sigla
    assert data['txtLocal'] == casa.endereco
