import pytest
from django.core.urlresolvers import reverse
from model_mommy import mommy

from sapl.parlamentares.models import (Dependente, Filiacao, Legislatura,
                                       Mandato, Parlamentar, Partido,
                                       TipoDependente)


@pytest.mark.django_db(transaction=False)
def test_cadastro_parlamentar(admin_client):
    legislatura = mommy.make(Legislatura)

    url = reverse('sapl.parlamentares:parlamentar_create')
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, {'nome_completo': 'Teresa Barbosa',
                                       'nome_parlamentar': 'Terezinha',
                                       'sexo': 'F',
                                       'ativo': 'True',
                                       'legislatura': legislatura.id,
                                       'data_expedicao_diploma': '2001-01-01'},
                                 follow=True)

    [parlamentar] = Parlamentar.objects.all()
    assert parlamentar.nome_parlamentar == 'Terezinha'
    assert parlamentar.sexo == 'F'
    assert parlamentar.ativo is True
    # o primeiro mandato é criado
    [mandato] = Mandato.objects.all()
    assert mandato.parlamentar == parlamentar
    assert str(mandato.data_expedicao_diploma) == '2001-01-01'
    assert mandato.legislatura == legislatura
    assert mandato.data_fim_mandato == legislatura.data_fim


@pytest.mark.django_db(transaction=False)
def test_incluir_parlamentar_errors(admin_client):
    url = reverse('sapl.parlamentares:parlamentar_create')
    response = admin_client.post(url)
    erros_esperados = {campo: ['Este campo é obrigatório.']
                       for campo in ['legislatura',
                                     'data_expedicao_diploma',
                                     'nome_parlamentar',
                                     'nome_completo',
                                     'sexo',
                                     ]}
    assert response.context_data['form'].errors == erros_esperados


@pytest.mark.django_db(transaction=False)
def test_filiacao_submit(admin_client):
    mommy.make(Parlamentar, pk=14)
    mommy.make(Partido, pk=32)

    admin_client.post(reverse('sapl.parlamentares:filiacao_create',
                              kwargs={'pk': 14}),
                      {'partido': 32,
                       'data': '2016-03-22',
                       'salvar': 'salvar'},
                      follow=True)

    filiacao = Filiacao.objects.first()
    assert 32 == filiacao.partido.pk


@pytest.mark.django_db(transaction=False)
def test_dependente_submit(admin_client):
    mommy.make(Parlamentar, pk=14)
    mommy.make(Partido, pk=32)
    mommy.make(TipoDependente, pk=3)

    admin_client.post(reverse('sapl.parlamentares:dependente_create',
                              kwargs={'pk': 14}),
                      {'nome': 'Eduardo',
                       'tipo': 3,
                       'sexo': 'M',
                       'salvar': 'salvar'},
                      follow=True)

    dependente = Dependente.objects.first()
    assert 3 == dependente.tipo.pk
    assert 'Eduardo' == dependente.nome


@pytest.mark.django_db(transaction=False)
def test_form_errors_dependente(admin_client):
    mommy.make(Parlamentar, pk=14)
    response = admin_client.post(
        reverse('sapl.parlamentares:dependente_create',
                kwargs={'pk': 14}),
        {'salvar': 'salvar'},
        follow=True)

    assert (response.context_data['form'].errors['nome'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['tipo'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['sexo'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_form_errors_filiacao(admin_client):
    mommy.make(Parlamentar, pk=14)

    response = admin_client.post(reverse('sapl.parlamentares:filiacao_create',
                                         kwargs={'pk': 14}),
                                 {'partido': '',
                                  'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['partido'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['data'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_mandato_submit(admin_client):
    mommy.make(Parlamentar, pk=14)
    mommy.make(Legislatura, pk=5)

    admin_client.post(reverse('sapl.parlamentares:mandato_create',
                              kwargs={'pk': 14}),
                      {'parlamentar': 14,  # hidden field
                       'legislatura': 5,
                       'data_fim_mandato': '2016-01-01',
                       'data_expedicao_diploma': '2016-03-22',
                       'observacao': 'Observação do mandato',
                       'salvar': 'salvar'},
                      follow=True)

    mandato = Mandato.objects.first()
    assert 'Observação do mandato' == mandato.observacao


@pytest.mark.django_db(transaction=False)
def test_form_errors_mandato(admin_client):
    mommy.make(Parlamentar, pk=14)
    response = admin_client.post(reverse('sapl.parlamentares:mandato_create',
                                         kwargs={'pk': 14}),
                                 {'legislatura': '',
                                  'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['legislatura'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['data_fim_mandato'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['data_expedicao_diploma'] ==
            ['Este campo é obrigatório.'])
