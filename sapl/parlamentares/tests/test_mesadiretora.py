import pytest
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from model_bakery import baker

from sapl.parlamentares.forms import ComposicaoMesaForm, MesaDiretoraForm
from sapl.parlamentares.models import ComposicaoMesa, MesaDiretora


def test_mesadiretora_form_invalido():
    form = MesaDiretoraForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['titulo'] == [_('Este campo é obrigatório.')]
    assert errors['data_inicio'] == [_('Este campo é obrigatório.')]
    assert errors['data_fim'] == [_('Este campo é obrigatório.')]
    assert errors['legislatura'] == [_('Este campo é obrigatório.')]


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_form_data_inicio_maior_que_data_fim():
    legislatura = baker.make('parlamentares.Legislatura')

    form = MesaDiretoraForm(data={
        'titulo': 'Mesa Diretora 2021-2022',
        'data_inicio': '2022-01-01',
        'data_fim': '2021-12-31',
        'legislatura': legislatura.id,
    })

    assert not form.is_valid()
    errors = form.errors
    assert errors['__all__'] == [_('A data de início deve ser anterior à data de fim.')]


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_form_valido():
    legislatura = baker.make('parlamentares.Legislatura')

    form = MesaDiretoraForm(data={
        'titulo': 'Mesa Diretora 2021-2022',
        'data_inicio': '2021-01-01',
        'data_fim': '2022-12-31',
        'legislatura': legislatura.id,
    })

    assert form.is_valid()

@pytest.mark.django_db(transaction=False)
def test_mesadiretora_form_intersecao():
    legislatura = baker.make('parlamentares.Legislatura')
    mesa_existente = baker.make(
        'parlamentares.MesaDiretora',
        legislatura=legislatura,
        titulo='Mesa Diretora 2021-2022',
        data_inicio='2021-01-01',
        data_fim='2022-12-31')

    form = MesaDiretoraForm(data={
        'titulo': 'Mesa Diretora 2022-2023',
        'data_inicio': '2022-01-01',
        'data_fim': '2023-12-31',
        'legislatura': legislatura.id,
    })

    assert not form.is_valid()
    errors = form.errors
    assert errors['__all__'] == [_('As datas da mesa diretora se sobrepõem com outra mesa diretora existente.')]


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_form_data_fora_da_legislatura():
    legislatura = baker.make(
        'parlamentares.Legislatura',
        data_inicio='2021-01-01',
        data_fim='2024-12-31')

    form = MesaDiretoraForm(data={
        'titulo': 'Mesa Diretora 2020-2021',
        'data_inicio': '2020-01-01',
        'data_fim': '2021-12-31',
        'legislatura': legislatura.id,
    })

    assert not form.is_valid()
    errors = form.errors
    assert errors['__all__'] == [_('As datas da mesa diretora devem estar dentro do período da legislatura.')]


def test_composicaomesa_form():
    form = ComposicaoMesaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['parlamentar'] == [_('Este campo é obrigatório.')]
    assert errors['cargo'] == [_('Este campo é obrigatório.')]
    assert errors['mesa_diretora'] == [_('Este campo é obrigatório.')]



@pytest.mark.django_db(transaction=False)
def test_composicaomesa_form_valido():
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')

    form = ComposicaoMesaForm(data={
        'parlamentar': parlamentar.id,
        'cargo': cargo.id,
        'mesa_diretora': mesa_diretora.id,
    })

    assert form.is_valid()

@pytest.mark.django_db(transaction=False)
def test_composicaomesa_form_parlamentar_ocupando_cargo_na_mesma_mesa():
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo1 = baker.make('parlamentares.CargoMesa')
    cargo2 = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')

    # Cria uma composição de mesa existente com o mesmo parlamentar e mesa
    ComposicaoMesa.objects.create(
        parlamentar=parlamentar,
        cargo=cargo1,
        mesa_diretora=mesa_diretora
    )

    form = ComposicaoMesaForm(data={
        'parlamentar': parlamentar.id,
        'cargo': cargo2.id,
        'mesa_diretora': mesa_diretora.id,
    })

    assert not form.is_valid()
    errors = form.errors
    assert errors['__all__'] == [_('Parlamentar já ocupa um cargo nesta mesa diretora.')]


@pytest.mark.django_db(transaction=False)
def test_composicaomesa_form_parlamentar_cargo_unico_mesma_mesa():
    parlamentar1 = baker.make('parlamentares.Parlamentar')
    parlamentar2 = baker.make('parlamentares.Parlamentar')

    cargo = baker.make('parlamentares.CargoMesa', unico=True)

    mesa_diretora = baker.make('parlamentares.MesaDiretora')

    mandato1 = baker.make('parlamentares.Mandato', parlamentar=parlamentar1, legislatura=mesa_diretora.legislatura)
    mandato2 = baker.make('parlamentares.Mandato', parlamentar=parlamentar2, legislatura=mesa_diretora.legislatura)

    # Cria uma composição de mesa existente com o cargo único
    ComposicaoMesa.objects.create(
        parlamentar=parlamentar1,
        cargo=cargo,
        mesa_diretora=mesa_diretora
    )

    form = ComposicaoMesaForm(data={
        'parlamentar': parlamentar2.id,
        'cargo': cargo.id,
        'mesa_diretora': mesa_diretora.id,
    }, initial={
        'mesa_diretora': mesa_diretora,
    })

    assert not form.is_valid()
    errors = form.errors
    assert errors['__all__'] == [_('Cargo único já ocupado por outro parlamentar.')]


@pytest.mark.django_db(transaction=False)
def test_composicaomesa_form_view_create(admin_client):
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')
    mandato = baker.make(
        'parlamentares.Mandato',
        parlamentar=parlamentar,
        legislatura=mesa_diretora.legislatura)

    response = admin_client.post(reverse('sapl.parlamentares:composicaomesa_create', kwargs={'pk': mesa_diretora.id}), data={
        'parlamentar': parlamentar.id,
        'cargo': cargo.id,
        'mesa_diretora': mesa_diretora.id,
    })

    assert ComposicaoMesa.objects.filter(parlamentar=parlamentar, cargo=cargo, mesa_diretora=mesa_diretora).exists()

@pytest.mark.django_db(transaction=False)
def test_composicaomesa_form_view_update(admin_client):
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')
    mandato = baker.make(
        'parlamentares.Mandato',
        parlamentar=parlamentar,
        legislatura=mesa_diretora.legislatura)

    composicao = ComposicaoMesa.objects.create(
        parlamentar=parlamentar,
        cargo=cargo,
        mesa_diretora=mesa_diretora
    )

    new_cargo = baker.make('parlamentares.CargoMesa')

    response = admin_client.post(reverse('sapl.parlamentares:composicaomesa_update', kwargs={'pk': composicao.id}), data={
        'parlamentar': parlamentar.id,
        'cargo': new_cargo.id,
        'mesa_diretora': mesa_diretora.id,
    })

    composicao.refresh_from_db()
    assert composicao.cargo == new_cargo