import pytest
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from sapl.parlamentares.forms import (FrenteForm, LegislaturaForm, MandatoForm)
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
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['tipo'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['sexo'] ==
            [_('Este campo é obrigatório.')])


@pytest.mark.django_db(transaction=False)
def test_form_errors_filiacao(admin_client):
    mommy.make(Parlamentar, pk=14)

    response = admin_client.post(reverse('sapl.parlamentares:filiacao_create',
                                         kwargs={'pk': 14}),
                                 {'partido': '',
                                  'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['partido'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['data'] ==
            [_('Este campo é obrigatório.')])


@pytest.mark.django_db(transaction=False)
def test_mandato_submit(admin_client):
    mommy.make(Parlamentar, pk=14)
    mommy.make(Legislatura, pk=5)

    admin_client.post(reverse('sapl.parlamentares:mandato_create',
                              kwargs={'pk': 14}),
                      {'parlamentar': 14,  # hidden field
                       'legislatura': 5,
                       'data_expedicao_diploma': '2016-03-22',
                       'observacao': 'Observação do mandato',
                       'salvar': 'salvar'},
                      follow=True)

    mandato = Mandato.objects.first()
    assert str(_('Observação do mandato')) == str(_(mandato.observacao))


@pytest.mark.django_db(transaction=False)
def test_form_errors_mandato(admin_client):
    mommy.make(Parlamentar, pk=14)
    response = admin_client.post(reverse('sapl.parlamentares:mandato_create',
                                         kwargs={'pk': 14}),
                                 {'legislatura': '',
                                  'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['legislatura'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['data_expedicao_diploma'] ==
            [_('Este campo é obrigatório.')])


def test_mandato_form_invalido():

    form = MandatoForm(data={})

    assert not form.is_valid()

    errors = form.errors
    assert errors['legislatura'] == [_('Este campo é obrigatório.')]
    assert errors['parlamentar'] == [_('Este campo é obrigatório.')]
    assert errors['data_expedicao_diploma'] == [_('Este campo é obrigatório.')]


@pytest.mark.django_db(transaction=False)
def test_mandato_form_duplicado():
    parlamentar = mommy.make(Parlamentar, pk=1)
    legislatura = mommy.make(Legislatura, pk=1)

    Mandato.objects.create(parlamentar=parlamentar,
                           legislatura=legislatura,
                           data_expedicao_diploma='2017-07-25')

    form = MandatoForm(data={
        'parlamentar': str(parlamentar.pk),
        'legislatura': str(legislatura.pk),
        'data_expedicao_diploma': '01/07/2015'
    })

    assert not form.is_valid()

    assert form.errors['__all__'] == [
        _('Mandato nesta legislatura já existe.')]


@pytest.mark.django_db(transaction=False)
def test_mandato_form_datas_invalidas():
    parlamentar = mommy.make(Parlamentar, pk=1)
    legislatura = mommy.make(Legislatura, pk=1,
                             data_inicio='2017-01-01',
                             data_fim='2021-12-31')

    form = MandatoForm(data={
        'parlamentar': str(parlamentar.pk),
        'legislatura': str(legislatura.pk),
        'data_expedicao_diploma': '2016-11-01',
        'data_inicio_mandato': '2016-12-12',
        'data_fim_mandato': '2019-10-09'
    })

    assert not form.is_valid()
    assert form.errors['__all__'] == \
        ["Data início mandato fora do intervalo de legislatura informada"]

    form = MandatoForm(data={
        'parlamentar': str(parlamentar.pk),
        'legislatura': str(legislatura.pk),
        'data_expedicao_diploma': '2016-11-01',
        'data_inicio_mandato': '2017-02-02',
        'data_fim_mandato': '2022-01-01'
    })

    assert not form.is_valid()
    assert form.errors['__all__'] == \
        ["Data fim mandato fora do intervalo de legislatura informada"]


def test_legislatura_form_invalido():

    legislatura_form = LegislaturaForm(data={})

    assert not legislatura_form.is_valid()

    errors = legislatura_form.errors

    errors['numero'] == [_('Este campo é obrigatório.')]
    errors['data_inicio'] == [_('Este campo é obrigatório.')]
    errors['data_fim'] == [_('Este campo é obrigatório.')]
    errors['data_eleicao'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 4


def test_legislatura_form_datas_invalidas():

    legislatura_form = LegislaturaForm(data={'numero': '1',
                                             'data_inicio': '2017-02-01',
                                             'data_fim': '2021-12-31',
                                             'data_eleicao': '2017-02-01'
                                             })

    assert not legislatura_form.is_valid()

    expected = \
        _("Data eleição não pode ser inferior a data início da legislatura")
    assert legislatura_form.errors['__all__'] == [expected]

    legislatura_form = LegislaturaForm(data={'numero': '1',
                                             'data_inicio': '2017-02-01',
                                             'data_fim': '2017-01-01',
                                             'data_eleicao': '2016-11-01'
                                             })

    assert not legislatura_form.is_valid()

    assert legislatura_form.errors['__all__'] == \
        [_("Intervalo de início e fim inválido para legislatura.")]

@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_frente_form():
    form = FrenteForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['nome'] == [_('Este campo é obrigatório.')]
    assert errors['data_criacao'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 2


@pytest.mark.django_db(transaction=False)
def test_frente_form_valido():
    parlamentares = mommy.make(Parlamentar)

    form = FrenteForm(data={'nome': 'Nome da Frente',
                            'parlamentar': str(parlamentares.pk),
                            'data_criacao': '10/11/2017',
                            'data_extincao': '10/12/2017',
                            'descricao': 'teste'
                            })

    assert form.is_valid()
