import pytest
from datetime import date

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from model_bakery import baker

from sapl.parlamentares.forms import ComposicaoMesaForm, MesaDiretoraForm
from sapl.parlamentares.models import ComposicaoMesa, MesaDiretora


# =====================================================================
# Testes de validação a nível de Model — MesaDiretora
# =====================================================================

@pytest.mark.django_db(transaction=False)
def test_mesadiretora_model_clean_data_inicio_maior_que_data_fim():
    legislatura = baker.make(
        'parlamentares.Legislatura',
        data_inicio=date(2021, 1, 1),
        data_fim=date(2024, 12, 31)
    )
    mesa = MesaDiretora(
        titulo='Mesa',
        data_inicio=date(2022, 1, 1),
        data_fim=date(2021, 12, 31),
        legislatura=legislatura
    )
    with pytest.raises(ValidationError, match='A data de início deve ser anterior e/ou igual à data de fim.'):
        mesa.clean()


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_model_clean_data_fora_da_legislatura():
    legislatura = baker.make(
        'parlamentares.Legislatura',
        data_inicio=date(2021, 1, 1),
        data_fim=date(2024, 12, 31)
    )
    mesa = MesaDiretora(
        titulo='Mesa',
        data_inicio=date(2020, 1, 1),
        data_fim=date(2021, 12, 31),
        legislatura=legislatura
    )
    with pytest.raises(ValidationError, match='As datas da mesa diretora devem estar dentro do período da legislatura.'):
        mesa.clean()


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_model_clean_intersecao():
    legislatura = baker.make(
        'parlamentares.Legislatura',
        data_inicio=date(2021, 1, 1),
        data_fim=date(2024, 12, 31)
    )
    baker.make(
        'parlamentares.MesaDiretora',
        legislatura=legislatura,
        titulo='Mesa Existente',
        data_inicio=date(2021, 1, 1),
        data_fim=date(2022, 12, 31)
    )
    mesa = MesaDiretora(
        titulo='Nova Mesa',
        data_inicio=date(2022, 1, 1),
        data_fim=date(2023, 12, 31),
        legislatura=legislatura
    )
    with pytest.raises(ValidationError, match='As datas da mesa diretora se sobrepõem com outra mesa diretora existente.'):
        mesa.clean()


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_model_clean_valido():
    legislatura = baker.make(
        'parlamentares.Legislatura',
        data_inicio=date(2021, 1, 1),
        data_fim=date(2024, 12, 31)
    )
    mesa = MesaDiretora(
        titulo='Mesa',
        data_inicio=date(2021, 1, 1),
        data_fim=date(2022, 12, 31),
        legislatura=legislatura
    )
    mesa.clean()  # não deve lançar exceção


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_model_full_clean_sem_data_inicio():
    legislatura = baker.make(
        'parlamentares.Legislatura',
        data_inicio=date(2021, 1, 1),
        data_fim=date(2024, 12, 31)
    )
    mesa = MesaDiretora(
        titulo='Mesa',
        data_fim=date(2022, 12, 31),
        legislatura=legislatura
    )
    with pytest.raises(ValidationError) as exc_info:
        mesa.full_clean()

    assert 'data_inicio' in exc_info.value.message_dict
    assert exc_info.value.message_dict['data_inicio'] == [_('Este campo não pode ser nulo.')]


# =====================================================================
# Testes de validação a nível de Model — ComposicaoMesa
# =====================================================================

@pytest.mark.django_db(transaction=False)
def test_composicaomesa_model_clean_parlamentar_duplicado():
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo1 = baker.make('parlamentares.CargoMesa')
    cargo2 = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')

    ComposicaoMesa.objects.create(
        parlamentar=parlamentar, cargo=cargo1, mesa_diretora=mesa_diretora
    )

    composicao = ComposicaoMesa(
        parlamentar=parlamentar, cargo=cargo2, mesa_diretora=mesa_diretora
    )
    with pytest.raises(ValidationError, match='Parlamentar já ocupa um cargo nesta mesa diretora.'):
        composicao.clean()


@pytest.mark.django_db(transaction=False)
def test_composicaomesa_model_clean_cargo_unico():
    parlamentar1 = baker.make('parlamentares.Parlamentar')
    parlamentar2 = baker.make('parlamentares.Parlamentar')
    cargo = baker.make('parlamentares.CargoMesa', unico=True)
    mesa_diretora = baker.make('parlamentares.MesaDiretora')

    ComposicaoMesa.objects.create(
        parlamentar=parlamentar1, cargo=cargo, mesa_diretora=mesa_diretora
    )

    composicao = ComposicaoMesa(
        parlamentar=parlamentar2, cargo=cargo, mesa_diretora=mesa_diretora
    )
    with pytest.raises(ValidationError, match='Cargo único já ocupado por outro parlamentar.'):
        composicao.clean()


@pytest.mark.django_db(transaction=False)
def test_composicaomesa_model_clean_valido():
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')

    composicao = ComposicaoMesa(
        parlamentar=parlamentar, cargo=cargo, mesa_diretora=mesa_diretora
    )
    composicao.clean()  # não deve lançar exceção


# =====================================================================
# Testes de validação via Form — MesaDiretora
# =====================================================================

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
    legislatura = baker.make(
        'parlamentares.Legislatura',
        data_inicio='2021-01-01',
        data_fim='2024-12-31'
    )

    form = MesaDiretoraForm(data={
        'titulo': 'Mesa Diretora 2021-2022',
        'data_inicio': '2022-01-01',
        'data_fim': '2021-12-31',
        'legislatura': legislatura.id,
    })

    assert not form.is_valid()
    errors = form.errors
    assert errors['__all__'] == [_('A data de início deve ser anterior e/ou igual à data de fim.')]


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_form_valido():
    legislatura = baker.make(
        'parlamentares.Legislatura',
        data_inicio='2021-01-01',
        data_fim='2024-12-31'
        )

    form = MesaDiretoraForm(data={
        'titulo': 'Mesa Diretora 2021-2022',
        'data_inicio': '2021-01-01',
        'data_fim': '2022-12-31',
        'legislatura': legislatura.id,
    })

    assert form.is_valid()

@pytest.mark.django_db(transaction=False)
def test_mesadiretora_form_intersecao():
    legislatura = baker.make(
        'parlamentares.Legislatura',
        data_inicio='2021-01-01',
        data_fim='2024-12-31'
    )
    baker.make(
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


# =====================================================================
# Testes de validação via Form — ComposicaoMesa
# =====================================================================

@pytest.mark.django_db(transaction=False)
def test_composicaomesa_form_invalido():
    mesa_diretora = baker.make('parlamentares.MesaDiretora')
    form = ComposicaoMesaForm(data={}, initial={'mesa_diretora': mesa_diretora})

    assert not form.is_valid()

    errors = form.errors

    assert errors['parlamentar'] == [_('Este campo é obrigatório.')]
    assert errors['cargo'] == [_('Este campo é obrigatório.')]


@pytest.mark.django_db(transaction=False)
def test_composicaomesa_form_valido():
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')
    baker.make(
        'parlamentares.Mandato',
        parlamentar=parlamentar,
        legislatura=mesa_diretora.legislatura)

    form = ComposicaoMesaForm(data={
        'parlamentar': parlamentar.id,
        'cargo': cargo.id,
    }, initial={
        'mesa_diretora': mesa_diretora,
    })

    assert form.is_valid()

@pytest.mark.django_db(transaction=False)
def test_composicaomesa_form_parlamentar_ocupando_cargo_na_mesma_mesa():
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo1 = baker.make('parlamentares.CargoMesa')
    cargo2 = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')
    baker.make(
        'parlamentares.Mandato',
        parlamentar=parlamentar,
        legislatura=mesa_diretora.legislatura)

    ComposicaoMesa.objects.create(
        parlamentar=parlamentar,
        cargo=cargo1,
        mesa_diretora=mesa_diretora
    )

    form = ComposicaoMesaForm(data={
        'parlamentar': parlamentar.id,
        'cargo': cargo2.id,
    }, initial={
        'mesa_diretora': mesa_diretora,
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

    baker.make('parlamentares.Mandato', parlamentar=parlamentar1, legislatura=mesa_diretora.legislatura)
    baker.make('parlamentares.Mandato', parlamentar=parlamentar2, legislatura=mesa_diretora.legislatura)

    ComposicaoMesa.objects.create(
        parlamentar=parlamentar1,
        cargo=cargo,
        mesa_diretora=mesa_diretora
    )

    form = ComposicaoMesaForm(data={
        'parlamentar': parlamentar2.id,
        'cargo': cargo.id,
    }, initial={
        'mesa_diretora': mesa_diretora,
    })

    assert not form.is_valid()
    errors = form.errors
    assert errors['__all__'] == [_('Cargo único já ocupado por outro parlamentar.')]


# =====================================================================
# Testes de integração via View — ComposicaoMesa
# =====================================================================

@pytest.mark.django_db(transaction=False)
def test_composicaomesa_form_view_create(admin_client):
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')
    baker.make(
        'parlamentares.Mandato',
        parlamentar=parlamentar,
        legislatura=mesa_diretora.legislatura)

    response = admin_client.post(reverse('sapl.parlamentares:composicaomesa_create', kwargs={'pk': mesa_diretora.id}), data={
        'parlamentar': parlamentar.id,
        'cargo': cargo.id,
    })

    assert response.status_code == 302  # Redirecionamento após criação bem-sucedida
    assert ComposicaoMesa.objects.filter(parlamentar=parlamentar, cargo=cargo, mesa_diretora=mesa_diretora).exists()

@pytest.mark.django_db(transaction=False)
def test_composicaomesa_form_view_update(admin_client):
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')
    baker.make(
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
    })

    composicao.refresh_from_db()
    assert response.status_code == 302  # Redirecionamento após atualização bem-sucedida
    assert composicao.cargo == new_cargo

@pytest.mark.django_db(transaction=False)
def test_mesadiretora_filter_set_sem_get(client):
    # MesaDiretoraFilterSet deve retornar apenas a legislatura atual quando não há parâmetros GET

    legislatura_antiga = baker.make('parlamentares.Legislatura', data_inicio='2017-01-01', data_fim='2020-12-31')
    baker.make('parlamentares.MesaDiretora', legislatura=legislatura_antiga, data_inicio='2017-01-01', data_fim='2018-12-31')

    legislatura_atual = baker.make('parlamentares.Legislatura', data_inicio='2021-01-01', data_fim='2024-12-31')
    baker.make('parlamentares.MesaDiretora', legislatura=legislatura_atual, data_inicio='2021-01-01', data_fim='2022-12-31')
    mesa_at2 = baker.make('parlamentares.MesaDiretora', legislatura=legislatura_atual, data_inicio='2022-01-01', data_fim='2023-12-31')

    response = client.get(reverse('sapl.parlamentares:mesadiretora_list'))
    assert response.status_code == 200
    assert response.context['filter'].qs.count() == 2
    assert response.context['filter'].qs.first() == mesa_at2

@pytest.mark.django_db(transaction=False)
def test_mesadiretora_filter_set_get_mesa_404(client):
    # MesaDiretoraFilterSet deve retornar 404 quando o parâmetro GET 'mesa' não corresponder a nenhuma mesa existente

    response = client.get(reverse('sapl.parlamentares:mesadiretora_list'), {'mesa': 9999})
    assert response.status_code == 404

@pytest.mark.django_db(transaction=False)
def test_mesadiretora_filter_set_get_mesa(client):
    # MesaDiretoraFilterSet deve retornar a mesa correspondente quando o parâmetro GET 'mesa' corresponder a uma mesa existente

    legislatura_atual = baker.make('parlamentares.Legislatura', data_inicio='2021-01-01', data_fim='2024-12-31')
    mesa = baker.make('parlamentares.MesaDiretora', legislatura=legislatura_atual, data_inicio='2021-01-01', data_fim='2022-12-31')

    response = client.get(reverse('sapl.parlamentares:mesadiretora_list'), {'mesa': mesa.id})
    assert response.status_code == 200
    assert response.context['filter'].qs.count() == 1
    assert response.context['filter'].qs.first() == mesa

@pytest.mark.django_db(transaction=False)
def test_mesadiretora_filter_set_get_legislatura(client):
    # MesaDiretoraFilterSet deve retornar apenas as mesas correspondentes à legislatura especificada no parâmetro GET 'legislatura'

    legislatura_antiga = baker.make('parlamentares.Legislatura', data_inicio='2017-01-01', data_fim='2020-12-31')
    baker.make('parlamentares.MesaDiretora', legislatura=legislatura_antiga, data_inicio='2017-01-01', data_fim='2018-12-31')

    legislatura_atual = baker.make('parlamentares.Legislatura', data_inicio='2021-01-01', data_fim='2024-12-31')
    mesa_at1 = baker.make('parlamentares.MesaDiretora', legislatura=legislatura_atual, data_inicio='2021-01-01', data_fim='2022-12-31')
    mesa_at2 = baker.make('parlamentares.MesaDiretora', legislatura=legislatura_atual, data_inicio='2022-01-01', data_fim='2023-12-31')

    response = client.get(reverse('sapl.parlamentares:mesadiretora_list'), {'legislatura': legislatura_atual.id})
    assert response.status_code == 200
    assert response.context['filter'].qs.count() == 2
    assert mesa_at1 in response.context['filter'].qs
    assert mesa_at2 in response.context['filter'].qs

@pytest.mark.django_db(transaction=False)
def test_mesadiretora_filter_set_(client):
    # Uma legislatura com 3 mesas, testar as abas no html
    legislatura = baker.make('parlamentares.Legislatura', data_inicio='2021-01-01', data_fim='2024-12-31')
    _ = baker.make('parlamentares.MesaDiretora', legislatura=legislatura, data_inicio='2021-01-01', data_fim='2022-12-31')
    _ = baker.make('parlamentares.MesaDiretora', legislatura=legislatura, data_inicio='2022-01-01', data_fim='2023-12-31')
    _ = baker.make('parlamentares.MesaDiretora', legislatura=legislatura, data_inicio='2023-01-01', data_fim='2024-12-31')

    response = client.get(reverse('sapl.parlamentares:mesadiretora_list'))
    assert response.status_code == 200
    assert response.context['filter'].qs.count() == 3

    ids_mesas = [f'id="tab-mesa-{mesa.id}"' for mesa in response.context['filter'].qs]

    for id_mesa in ids_mesas:
        assert id_mesa in response.content.decode('utf-8')
