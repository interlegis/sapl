from model_bakery import baker
import pytest
import json
from sapl.parlamentares.models import Legislatura, ComposicaoMesa, Parlamentar,\
 SessaoLegislativa, CargoMesa
from django.urls import reverse
from sapl.api import views

@pytest.mark.django_db(transaction=False)
def test_get_mesa_diretora(admin_client):
    #criar legislatura, sessao e parlamentares
    parlamentar = baker.make(Parlamentar, nome_parlamentar='Joseph Joestar', id=8, fotografia=None)

    legislatura = baker.make(Legislatura, id=34)

    sessao = baker.make(SessaoLegislativa, legislatura=legislatura, id=44)

    cargo = baker.make(CargoMesa, descricao="presidente")

    #passar informações para a composicao_mesa
    mesa = baker.make(ComposicaoMesa, parlamentar=parlamentar,
    sessao_legislativa=sessao, cargo=cargo)

    #Verifica se a mesa foi criada
    mesa_diretora = ComposicaoMesa.objects.get(sessao_legislativa=sessao, parlamentar=parlamentar)

    #Testa o POST
    jresponse = admin_client.post(reverse('sapl.api:get_mesa_diretora'))
    assert jresponse.status_code == 200

