import pytest
from django.core.urlresolvers import reverse
from model_mommy import mommy

from sapl.comissoes.models import Comissao, Composicao, Periodo, TipoComissao
from sapl.parlamentares.models import Filiacao, Parlamentar, Partido


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
def test_incluir_parlamentar_errors(admin_client):
    comissao = make_comissao()
    composicao = make_composicao(comissao)

    response = admin_client.post(reverse('sapl.comissoes:participacao_create',
                                         kwargs={'pk': composicao.pk}),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['parlamentar'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['cargo'] ==
            ['Este campo é obrigatório.'])
    assert (response.context_data['form'].errors['data_designacao'] ==
            ['Este campo é obrigatório.'])


@pytest.mark.django_db(transaction=False)
def test_incluir_comissao_submit(admin_client):
    tipo = mommy.make(TipoComissao,
                      sigla='T',
                      nome='Teste')

    response = admin_client.post(reverse('sapl.comissoes:comissao_create'),
                                 {'tipo': tipo.pk,
                                  'nome': 'Comissão Teste',
                                  'sigla': 'CT',
                                  'data_criacao': '2016-03-22',
                                  'unidade_deliberativa': True,
                                  'salvar': 'salvar'
                                  },
                                 follow=True)
    assert response.status_code == 200

    comissao = Comissao.objects.first()
    assert comissao.nome == 'Comissão Teste'
    assert comissao.tipo == tipo


@pytest.mark.django_db(transaction=False)
def test_incluir_comissao_errors(admin_client):

    response = admin_client.post(reverse('sapl.comissoes:comissao_create'),
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
