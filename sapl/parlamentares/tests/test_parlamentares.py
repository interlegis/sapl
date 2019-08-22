import pytest
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy
from datetime import datetime

from sapl.parlamentares import forms
from sapl.parlamentares.forms import FrenteForm, LegislaturaForm, MandatoForm, AfastamentoParlamentarForm
from sapl.parlamentares.models import (Dependente, Filiacao, Legislatura,
                                       Mandato, Parlamentar, Partido,
                                       TipoDependente, TipoAfastamento,
                                       AfastamentoParlamentar)
from sapl.utils import verifica_afastamento_parlamentar


@pytest.mark.django_db(transaction=False)
def test_cadastro_parlamentar(admin_client):
    legislatura = mommy.make(Legislatura)

    url = reverse('sapl.parlamentares:parlamentar_create')
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, {'nome_completo': 'Teresa Barbosa',
                                       'nome_parlamentar': 'Terezinha',
                                       'sexo': 'F',
                                       'ativo': 'True'
                                       },
                                 follow=True)

    [parlamentar] = Parlamentar.objects.all()
    assert parlamentar.nome_parlamentar == 'Terezinha'
    assert parlamentar.sexo == 'F'
    assert parlamentar.ativo is True


@pytest.mark.django_db(transaction=False)
def test_incluir_parlamentar_errors(admin_client):
    url = reverse('sapl.parlamentares:parlamentar_create')
    response = admin_client.post(url)
    erros_esperados = {campo: ['Este campo é obrigatório.']
                       for campo in ['nome_parlamentar',
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
                       'data_inicio_mandato': \
                          Legislatura.objects.get(id=5).data_inicio,
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


def test_mandato_form_invalido():

    form = MandatoForm(data={})

    assert not form.is_valid()

    errors = form.errors
    assert errors['legislatura'] == [_('Este campo é obrigatório.')]
    assert errors['parlamentar'] == [_('Este campo é obrigatório.')]


@pytest.mark.django_db(transaction=False)
def test_mandato_form_duplicado():
    parlamentar = mommy.make(Parlamentar, pk=1)
    legislatura = mommy.make(Legislatura, pk=1)

    Mandato.objects.create(parlamentar=parlamentar,
                           legislatura=legislatura,
                           data_expedicao_diploma='2017-07-25',
                           data_inicio_mandato=legislatura.data_inicio,)

    form = MandatoForm(data={
        'parlamentar': str(parlamentar.pk),
        'legislatura': str(legislatura.pk),
        'data_expedicao_diploma': '01/07/2015',
        'data_inicio_mandato': legislatura.data_inicio,
        'titular':True,
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

    assert errors['numero'] == [_('Este campo é obrigatório.')]
    assert errors['data_inicio'] == [_('Este campo é obrigatório.')]
    assert errors['data_fim'] == [_('Este campo é obrigatório.')]
    assert errors['data_eleicao'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 4

@pytest.mark.django_db(transaction=False)
def test_legislatura_form_datas_invalidas():

        legislatura_form = LegislaturaForm(data={'numero': '1',
                                                'data_inicio': '2017-02-01',
                                                'data_fim': '2021-12-31',
                                                'data_eleicao': '2016-11-01'
                                                })

        assert legislatura_form.is_valid()

        legislatura_form = LegislaturaForm(data={'numero': '1',
                                             'data_inicio': '2017-02-01',
                                             'data_fim': '2021-12-31',
                                             'data_eleicao': '2017-02-01'
                                             })

        assert not legislatura_form.is_valid()

        expected = \
        _("A data início deve ser menor que a data fim "
          "e a data eleição deve ser menor que a data início")
        assert legislatura_form.errors['__all__'] == [expected]

        legislatura_form = LegislaturaForm(data={'numero': '1',
                                             'data_inicio': '2017-02-01',
                                             'data_fim': '2017-01-01',
                                             'data_eleicao': '2016-11-01'
                                             })

        assert not legislatura_form.is_valid()

        assert legislatura_form.errors['__all__'] == [expected]


@pytest.mark.django_db(transaction=False)
def test_legislatura_form_numeros_invalidos():

        legislatura_form = LegislaturaForm(data={'numero': '5',
                                                'data_inicio': '2017-02-01',
                                                'data_fim': '2021-12-31',
                                                'data_eleicao': '2016-11-01'
                                                })

        assert legislatura_form.is_valid()

        legislatura = mommy.make(Legislatura, pk=1,
                                 numero=5,
                                 data_inicio='2017-02-01',
                                 data_fim='2021-12-31',
                                 data_eleicao='2016-11-01')

        legislatura_form = LegislaturaForm(data={'numero': '6',
                                                'data_inicio': '2014-02-01',
                                                'data_fim': '2016-12-31',
                                                'data_eleicao': '2013-11-01'
                                                })

        assert not legislatura_form.is_valid()

        legislatura_form = LegislaturaForm(data={'numero': '4',
                                                'data_inicio': '2022-02-01',
                                                'data_fim': '2025-12-31',
                                                'data_eleicao': '2021-11-01'
                                                })

        assert not legislatura_form.is_valid()

        legislatura_form = LegislaturaForm(data={'numero': '5',
                                                'data_inicio': '2014-02-01',
                                                'data_fim': '2016-12-31',
                                                'data_eleicao': '2013-11-01'
                                                })
        legislatura_form.instance = legislatura

        assert legislatura_form.is_valid()

        legislatura = mommy.make(Legislatura, pk=2,
                                 numero=1,
                                 data_inicio='2002-02-01',
                                 data_fim='2005-12-31',
                                 data_eleicao='2001-11-01')
        
        legislatura2 = mommy.make(Legislatura, pk=3,
                                 numero=3,
                                 data_inicio='2008-02-01',
                                 data_fim='2011-12-31',
                                 data_eleicao='2007-11-01')

        legislatura_form = LegislaturaForm(data={'numero': '1',
                                                'data_inicio': '2010-02-01',
                                                'data_fim': '2013-12-31',
                                                'data_eleicao': '2009-11-01'
                                                })
        legislatura_form.instance = legislatura

        assert not legislatura_form.is_valid()


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


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_bancada_form():
    form = forms.BancadaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['legislatura'] == [_('Este campo é obrigatório.')]
    assert errors['nome'] == [_('Este campo é obrigatório.')]
    assert errors['data_criacao'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 3


def data(valor):
    return datetime.strptime(valor, '%Y-%m-%d').date()


@pytest.mark.django_db(transaction=False)
def test_bancada_form_valido():
    legislatura = mommy.make(Legislatura,
                             data_inicio=data('2017-11-10'),
                             data_fim=data('2017-12-31'),
                             )
    partido = mommy.make(Partido)

    form = forms.BancadaForm(data={'legislatura': str(legislatura.pk),
                                   'nome': 'Nome da Bancada',
                                   'partido': str(partido.pk),
                                   'data_criacao': '10/11/2017',
                                   'data_extincao': '10/12/2017',
                                   'descricao': 'teste'
                                   })

    assert form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_bancada_form_datas_invalidas():
    legislatura = mommy.make(Legislatura,
                             data_inicio=data('2017-11-10'),
                             data_fim=data('2017-12-31'),
                             )
    partido = mommy.make(Partido)

    form = forms.BancadaForm(data={'legislatura': str(legislatura.pk),
                                   'nome': 'Nome da Bancada',
                                   'partido': str(partido.pk),
                                   'data_criacao': '2016-11-01',
                                   'data_extincao': '2016-10-01',
                                   'descricao': 'teste'
                                   })
    assert not form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_afastamentos_form_datas_invalidas():
    parlamentar = mommy.make(Parlamentar)
    mandato = mommy.make(Mandato,
                         parlamentar = parlamentar,
                         data_inicio_mandato='2017-01-01',
                         data_fim_mandato='2021-12-31')
    tipo_afastamento = mommy.make(TipoAfastamento, 
                                  indicador= 'A', 
                                  pk=1)

    form = AfastamentoParlamentarForm(data={
        'parlamentar': parlamentar.pk,
        'mandato': mandato.pk,
        'data_inicio': '2016-12-12',
        'data_fim': '2019-10-09',
        'tipo_afastamento': tipo_afastamento.pk
    }, initial={'parlamentar': parlamentar.pk})

    assert not form.is_valid()
    assert form.errors['__all__'] == \
        ["Data início do afastamento anterior ao início do mandato informado."]

    form = AfastamentoParlamentarForm(data={
        'parlamentar': parlamentar.pk,
        'mandato': mandato.pk,
        'data_inicio': '2017-02-02',
        'data_fim': '2022-10-09',
        'tipo_afastamento': tipo_afastamento.pk
    }, initial={'parlamentar': parlamentar.pk})

    assert not form.is_valid()
    assert form.errors['__all__'] == \
        ["Data fim do afastamento posterior ao fim do mandato informado."]

    form = AfastamentoParlamentarForm(data={
        'parlamentar': parlamentar.pk,
        'mandato': mandato.pk,
        'data_inicio': '2017-02-02',
        'data_fim': '2015-10-09',
        'tipo_afastamento': tipo_afastamento.pk
    }, initial={'parlamentar': parlamentar.pk})

    assert not form.is_valid()
    assert form.errors['__all__'] == \
        ["Data fim do afastamento anterior à data início do afastamento."]

    form = AfastamentoParlamentarForm(data={
        'parlamentar': parlamentar.pk,
        'mandato': mandato.pk,
        'data_inicio': '2017-02-02',
        'tipo_afastamento': tipo_afastamento.pk
    }, initial={'parlamentar': parlamentar.pk})

    assert form.is_valid()

    form.save()
    assert AfastamentoParlamentar.objects.all().count() == 1

    form = AfastamentoParlamentarForm(data={
        'parlamentar': parlamentar.pk,
        'mandato': mandato.pk,
        'data_inicio': '2018-04-02',
        'data_fim': '2018-06-09',
        'tipo_afastamento': tipo_afastamento.pk
    }, initial={'parlamentar': parlamentar.pk})

    assert not form.is_valid()
    assert form.errors['__all__'] == \
        ["Existe Afastamento sem Data Fim."]

    afastamento = AfastamentoParlamentar.objects.first()
    afastamento.data_fim = '2017-04-02'
    afastamento.save()

    assert AfastamentoParlamentar.objects.first().data_fim == data('2017-04-02')

    form = AfastamentoParlamentarForm(data={
        'parlamentar': parlamentar.pk,
        'mandato': mandato.pk,
        'data_inicio': '2018-04-02',
        'data_fim': '2018-06-09',
        'tipo_afastamento': tipo_afastamento.pk
    }, initial={'parlamentar': parlamentar.pk})

    assert form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_afastamentos_form_campos_invalidos():
    parlamentar = mommy.make(Parlamentar)
    mandato = mommy.make(Mandato,
                         parlamentar = parlamentar,
                         data_inicio_mandato='2017-01-01',
                         data_fim_mandato='2021-12-31')
    tipo_afastamento = mommy.make(TipoAfastamento, 
                                  indicador= 'A', 
                                  pk=1)

    form = AfastamentoParlamentarForm(data={}, initial={'parlamentar': parlamentar.pk})

    assert not form.is_valid()

    assert form.errors['data_inicio'] == ["Este campo é obrigatório."]
    assert form.errors['mandato'] == ["Este campo é obrigatório."]
    assert form.errors['parlamentar'] == ["Este campo é obrigatório."]


@pytest.mark.django_db(transaction=False)
def test_parlamentar_esta_afastado():
    parlamentar = mommy.make(Parlamentar)
    mandato = mommy.make(Mandato,
                         parlamentar = parlamentar,
                         data_inicio_mandato='2017-01-01',
                         data_fim_mandato='2021-12-31')
    afastamento = AfastamentoParlamentar.objects.create(mandato=mandato, 
                                                        parlamentar=parlamentar,
                                                        data_inicio='2017-12-05',
                                                        data_fim='2017-12-12')
    assert verifica_afastamento_parlamentar(parlamentar, '2017-12-06')
    assert not verifica_afastamento_parlamentar(parlamentar, '2017-12-13')
    assert not verifica_afastamento_parlamentar(parlamentar, '2017-12-04')

    assert verifica_afastamento_parlamentar(parlamentar, '2017-12-06', '2017-12-11')
    assert verifica_afastamento_parlamentar(parlamentar, '2017-12-06', '2017-12-06')
    assert not verifica_afastamento_parlamentar(parlamentar, '2017-12-03', '2017-12-04')
    assert not verifica_afastamento_parlamentar(parlamentar, '2017-12-13', '2017-12-15')
    assert not verifica_afastamento_parlamentar(parlamentar, '2017-12-15', '2017-12-15')

    afastamento = AfastamentoParlamentar.objects.create(mandato=mandato, 
                                                        parlamentar=parlamentar,
                                                        data_inicio='2017-12-05')

    assert AfastamentoParlamentar.objects.all().count() == 2

    assert verifica_afastamento_parlamentar(parlamentar, '2017-12-06')
    assert not verifica_afastamento_parlamentar(parlamentar, '2017-12-13')
    assert not verifica_afastamento_parlamentar(parlamentar, '2017-12-04')

    assert verifica_afastamento_parlamentar(parlamentar, '2017-12-06', '2017-12-11')
    assert verifica_afastamento_parlamentar(parlamentar, '2017-12-06', '2017-12-06')
    assert not verifica_afastamento_parlamentar(parlamentar, '2017-12-03', '2017-12-04')
    assert verifica_afastamento_parlamentar(parlamentar, '2017-12-13', '2017-12-15')
