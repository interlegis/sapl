import pytest
from django.core.urlresolvers import reverse
from model_mommy import mommy

from comissoes.models import (CargoComissao, Comissao, Composicao,
                              Participacao, Periodo, TipoComissao)
from parlamentares.models import Filiacao, Parlamentar, Partido


def make_composicao(comissao):
    periodo = mommy.make(Periodo,
                         data_inicio='2016-01-01',
                         data_fim='2016-12-31')
    mommy.make(Composicao,
               periodo=periodo,
               comissao=comissao)
    return Composicao.objects.first()


def make_comissao():
    tipo = mommy.make(TipoComissao)
    mommy.make(Comissao,
               tipo=tipo,
               nome='Comissão Teste',
               sigla='CT',
               data_criacao='2016-03-22')
    return Comissao.objects.first()


def make_filiacao():
    partido = mommy.make(Partido,
                         nome='Partido Meu',
                         sigla='PM')
    parlamentar = mommy.make(Parlamentar,
                             nome_parlamentar='Eduardo',
                             nome_completo='Eduardo',
                             sexo='M',
                             ativo=True)
    mommy.make(Filiacao,
               data='2016-03-22',
               parlamentar=parlamentar,
               partido=partido)

    return Filiacao.objects.first()


@pytest.mark.django_db(transaction=False)
def test_incluir_parlamentar_submit(client):
    comissao = make_comissao()
    composicao = make_composicao(comissao)
    filiacao = make_filiacao()
    cargo = mommy.make(CargoComissao,
                       nome='Cargo',
                       unico=True)

    response = client.post(reverse('comissoes:comissao_parlamentar',
                                   kwargs={'pk': comissao.pk,
                                           'id': composicao.pk}),
                           {'parlamentar_id': filiacao.pk,
                            'cargo': cargo.pk,
                            'data_designacao': '2016-03-22',
                            'titular': True,
                            'salvar': 'salvar'},
                           follow=True)
    assert response.status_code == 200

    participacao = Participacao.objects.first()
    assert participacao.parlamentar == filiacao.parlamentar
    assert participacao.cargo.nome == 'Cargo'
    assert participacao.composicao == composicao


@pytest.mark.django_db(transaction=False)
def test_incluir_parlamentar_errors(client):
    comissao = make_comissao()
    composicao = make_composicao(comissao)

    response = client.post(reverse('comissoes:comissao_parlamentar',
                                   kwargs={'pk': comissao.pk,
                                           'id': composicao.pk}),
                           {'salvar': 'salvar'},
                           follow=True)

    assert (response.context_data['form'].errors['parlamentar_id'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['cargo'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['data_designacao'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_incluir_comissao_submit(client):
    tipo = mommy.make(TipoComissao,
                      sigla='T',
                      nome='Teste')

    response = client.post(reverse('comissoes:comissao_create'),
                           {'tipo': tipo.pk,
                            'nome': 'Comissão Teste',
                            'sigla': 'CT',
                            'data_criacao': '2016-03-22',
                            'salvar': 'salvar'},
                           follow=True)
    assert response.status_code == 200

    comissao = Comissao.objects.first()
    assert comissao.nome == 'Comissão Teste'
    assert comissao.tipo == tipo


@pytest.mark.django_db(transaction=False)
def test_incluir_comissao_errors(client):

    response = client.post(reverse('comissoes:comissao_create'),
                           {'salvar': 'salvar'},
                           follow=True)

    assert (response.context_data['form'].errors['tipo'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['nome'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['sigla'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['data_criacao'] ==
            ['Este campo é obrigatório.'])
