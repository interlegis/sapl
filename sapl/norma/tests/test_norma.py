import pytest
from django.core.urlresolvers import reverse
from model_mommy import mommy

from sapl.norma.models import NormaJuridica, TipoNormaJuridica


@pytest.mark.django_db(transaction=False)
def test_incluir_norma_submit(client):
    # Cria um tipo de norma
    tipo = mommy.make(TipoNormaJuridica,
                      sigla='T',
                      descricao='Teste')

    # Testa POST
    response = client.post(reverse('sapl.norma:normajuridica_create'),
                           {'tipo': tipo.pk,
                            'numero': '1',
                            'ano': '2016',
                            'data': '2016-03-22',
                            'esfera_federacao': 'E',
                            'ementa': 'Teste_Ementa',
                            'salvar': 'salvar'},
                           follow=True)
    assert response.status_code == 200

    norma = NormaJuridica.objects.first()
    assert norma.numero == 1
    assert norma.ano == 2016
    assert norma.tipo == tipo


@pytest.mark.django_db(transaction=False)
def test_incluir_norma_errors(client):

    response = client.post(reverse('sapl.norma:normajuridica_create'),
                           {'salvar': 'salvar'},
                           follow=True)

    assert (response.context_data['form'].errors['tipo'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['numero'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['ano'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['data'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['esfera_federacao'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['ementa'] ==
            ['Este campo é obrigatório.'])
