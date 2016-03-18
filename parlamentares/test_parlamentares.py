import pytest
from django.core.urlresolvers import reverse
from model_mommy import mommy

from .models import Legislatura, Parlamentar


@pytest.mark.django_db(transaction=False)
def test_cadastro_parlamentar(client):
    mommy.make(Legislatura, pk=5)

    response = client.get(reverse('parlamentares_cadastro', kwargs={'pk': 5}))
    assert response.status_code == 200

    response = client.post(reverse('parlamentares_cadastro', kwargs={'pk': 5}),
                           {'nome_completo': 'Teresa Barbosa',
                            'nome_parlamentar': 'Terezinha',
                            'sexo': 'F',
                            'ativo': 'True',
                            })
    parlamentar = Parlamentar.objects.first()
    assert "Terezinha" == parlamentar.nome_parlamentar
    if not parlamentar.ativo:
        pytest.fail("Parlamentar deve estar ativo")
