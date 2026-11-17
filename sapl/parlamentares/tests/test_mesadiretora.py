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

    baker.make('parlamentares.Mandato', parlamentar=parlamentar,
               legislatura=mesa_diretora.legislatura)

    composicao = ComposicaoMesa(
        parlamentar=parlamentar, cargo=cargo, mesa_diretora=mesa_diretora
    )
    composicao.clean()  # não deve lançar exceção


@pytest.mark.django_db(transaction=False)
def test_composicaomesa_model_clean_sem_mandato_na_legislatura():
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')
    # mandato em outra legislatura não vale
    baker.make('parlamentares.Mandato', parlamentar=parlamentar)

    composicao = ComposicaoMesa(
        parlamentar=parlamentar, cargo=cargo, mesa_diretora=mesa_diretora
    )
    with pytest.raises(ValidationError,
                       match='O parlamentar não tem mandato na legislatura'):
        composicao.clean()


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


# =====================================================================
# Testes da API — as regras do clean() valem também nas escritas
# =====================================================================

URL_API_MESA = '/api/parlamentares/mesadiretora/'
URL_API_COMPOSICAO = '/api/parlamentares/composicaomesa/'


@pytest.fixture
def api_client(db):
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient
    user = get_user_model().objects.create_superuser(
        username='admin_api_mesa', password='secret123', email='mesa@x.com')
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def legislatura_api(db):
    return baker.make(
        'parlamentares.Legislatura',
        numero=1,
        data_inicio=date(2021, 1, 1),
        data_fim=date(2024, 12, 31),
        data_eleicao=date(2020, 11, 15))


@pytest.fixture
def mesa_api(legislatura_api):
    return baker.make(
        'parlamentares.MesaDiretora',
        titulo='Mesa Diretora 2021/2022',
        legislatura=legislatura_api,
        data_inicio=date(2021, 1, 1),
        data_fim=date(2022, 12, 31))


def _post_mesa(client, legislatura, inicio, fim, titulo='Mesa via API'):
    return client.post(URL_API_MESA, {
        'titulo': titulo,
        'data_inicio': inicio,
        'data_fim': fim,
        'legislatura': legislatura.pk,
    }, format='json')


@pytest.mark.django_db(transaction=False)
def test_api_mesadiretora_valida(api_client, legislatura_api, mesa_api):
    response = _post_mesa(api_client, legislatura_api,
                          '2023-01-01', '2024-12-31')
    assert response.status_code == 201, response.content


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('inicio, fim, mensagem', [
    ('2022-06-01', '2023-06-30', 'se sobrepõem'),
    ('2024-06-01', '2023-01-01', 'data de início deve ser anterior'),
    ('2025-01-01', '2025-12-31', 'dentro do período da legislatura'),
])
def test_api_mesadiretora_invalida(api_client, legislatura_api, mesa_api,
                                   inicio, fim, mensagem):
    response = _post_mesa(api_client, legislatura_api, inicio, fim)
    assert response.status_code == 400
    assert mensagem in ' '.join(response.json()['non_field_errors'])
    assert MesaDiretora.objects.count() == 1


@pytest.mark.django_db(transaction=False)
def test_api_mesadiretora_patch_so_descricao(api_client, mesa_api):
    response = api_client.patch(f'{URL_API_MESA}{mesa_api.pk}/',
                                {'descricao': 'Nova descrição'},
                                format='json')
    assert response.status_code == 200, response.content
    mesa_api.refresh_from_db()
    assert mesa_api.descricao == 'Nova descrição'


@pytest.mark.django_db(transaction=False)
def test_api_mesadiretora_patch_com_sobreposicao(api_client, legislatura_api,
                                                 mesa_api):
    outra = baker.make(
        'parlamentares.MesaDiretora',
        legislatura=legislatura_api,
        data_inicio=date(2023, 1, 1),
        data_fim=date(2024, 12, 31))
    response = api_client.patch(f'{URL_API_MESA}{mesa_api.pk}/',
                                {'data_fim': '2023-06-30'}, format='json')
    assert response.status_code == 400
    mesa_api.refresh_from_db()
    assert mesa_api.data_fim == date(2022, 12, 31)
    assert outra.data_inicio == date(2023, 1, 1)


def _parlamentar_com_mandato(legislatura):
    parlamentar = baker.make('parlamentares.Parlamentar')
    baker.make('parlamentares.Mandato', parlamentar=parlamentar,
               legislatura=legislatura)
    return parlamentar


@pytest.mark.django_db(transaction=False)
def test_api_composicaomesa_valida(api_client, mesa_api):
    cargo = baker.make('parlamentares.CargoMesa', unico=True)
    parlamentar = _parlamentar_com_mandato(mesa_api.legislatura)
    response = api_client.post(URL_API_COMPOSICAO, {
        'mesa_diretora': mesa_api.pk,
        'parlamentar': parlamentar.pk,
        'cargo': cargo.pk,
    }, format='json')
    assert response.status_code == 201, response.content


@pytest.mark.django_db(transaction=False)
def test_api_composicaomesa_cargo_unico_ocupado(api_client, mesa_api):
    cargo = baker.make('parlamentares.CargoMesa', unico=True)
    baker.make('parlamentares.ComposicaoMesa', mesa_diretora=mesa_api,
               cargo=cargo,
               parlamentar=_parlamentar_com_mandato(mesa_api.legislatura))
    response = api_client.post(URL_API_COMPOSICAO, {
        'mesa_diretora': mesa_api.pk,
        'parlamentar': _parlamentar_com_mandato(mesa_api.legislatura).pk,
        'cargo': cargo.pk,
    }, format='json')
    assert response.status_code == 400
    assert 'Cargo único já ocupado' in \
        ' '.join(response.json()['non_field_errors'])


@pytest.mark.django_db(transaction=False)
def test_api_composicaomesa_parlamentar_repetido(api_client, mesa_api):
    parlamentar = _parlamentar_com_mandato(mesa_api.legislatura)
    baker.make('parlamentares.ComposicaoMesa', mesa_diretora=mesa_api,
               parlamentar=parlamentar,
               cargo=baker.make('parlamentares.CargoMesa', unico=True))
    response = api_client.post(URL_API_COMPOSICAO, {
        'mesa_diretora': mesa_api.pk,
        'parlamentar': parlamentar.pk,
        'cargo': baker.make('parlamentares.CargoMesa', unico=True).pk,
    }, format='json')
    assert response.status_code == 400
    assert 'Parlamentar já ocupa um cargo' in \
        ' '.join(response.json()['non_field_errors'])


@pytest.mark.django_db(transaction=False)
def test_composicaomesa_parlamentar_com_dois_mandatos_na_legislatura(
        admin_client):
    """Suplente com mais de um mandato na legislatura aparece uma vez só
    no select e pode ser salvo (antes: opção repetida e 500)."""
    parlamentar = baker.make('parlamentares.Parlamentar')
    cargo = baker.make('parlamentares.CargoMesa')
    mesa_diretora = baker.make('parlamentares.MesaDiretora')
    baker.make('parlamentares.Mandato', parlamentar=parlamentar,
               legislatura=mesa_diretora.legislatura, titular=True)
    baker.make('parlamentares.Mandato', parlamentar=parlamentar,
               legislatura=mesa_diretora.legislatura, titular=False)

    form = ComposicaoMesaForm(
        data={'parlamentar': parlamentar.id, 'cargo': cargo.id},
        initial={'mesa_diretora': mesa_diretora})
    assert form.fields['parlamentar'].queryset.filter(
        pk=parlamentar.pk).count() == 1
    assert form.is_valid(), form.errors

    response = admin_client.post(
        reverse('sapl.parlamentares:composicaomesa_create',
                kwargs={'pk': mesa_diretora.id}),
        data={'parlamentar': parlamentar.id, 'cargo': cargo.id})
    assert response.status_code == 302
    assert ComposicaoMesa.objects.filter(
        parlamentar=parlamentar, mesa_diretora=mesa_diretora).count() == 1


@pytest.mark.django_db(transaction=False)
def test_api_composicaomesa_parlamentar_sem_mandato(api_client, mesa_api):
    parlamentar = baker.make('parlamentares.Parlamentar')
    response = api_client.post(URL_API_COMPOSICAO, {
        'mesa_diretora': mesa_api.pk,
        'parlamentar': parlamentar.pk,
        'cargo': baker.make('parlamentares.CargoMesa').pk,
    }, format='json')
    assert response.status_code == 400
    assert 'não tem mandato' in \
        ' '.join(response.json()['non_field_errors'])


# =====================================================================
# Bordas da regra de sobreposição (mesa de um dia e encosto)
# =====================================================================

@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('existente, nova, aceita', [
    # duas mesas longas que só encostam (r3715887423)
    ((date(2021, 1, 1), date(2022, 1, 10)),
     (date(2022, 1, 10), date(2022, 12, 31)), True),
    ((date(2022, 1, 10), date(2022, 12, 31)),
     (date(2021, 1, 1), date(2022, 1, 10)), True),
    # mesas longas sobrepostas
    ((date(2021, 1, 1), date(2022, 1, 10)),
     (date(2022, 1, 5), date(2022, 12, 31)), False),
    # mesas longas idênticas
    ((date(2021, 1, 1), date(2022, 1, 10)),
     (date(2021, 1, 1), date(2022, 1, 10)), False),
    # duas mesas de um dia idênticas
    ((date(2022, 3, 10), date(2022, 3, 10)),
     (date(2022, 3, 10), date(2022, 3, 10)), False),
    # mesa de um dia no último dia de uma mesa longa, nas duas ordens
    ((date(2022, 1, 1), date(2022, 3, 10)),
     (date(2022, 3, 10), date(2022, 3, 10)), True),
    ((date(2022, 3, 10), date(2022, 3, 10)),
     (date(2022, 1, 1), date(2022, 3, 10)), True),
    # mesa de um dia seguida de mesa longa no mesmo dia, nas duas ordens
    ((date(2022, 3, 10), date(2022, 3, 10)),
     (date(2022, 3, 10), date(2022, 12, 31)), True),
    ((date(2022, 3, 10), date(2022, 12, 31)),
     (date(2022, 3, 10), date(2022, 3, 10)), True),
    # mesa de um dia no meio de uma mesa longa, nas duas ordens
    ((date(2022, 1, 1), date(2022, 12, 31)),
     (date(2022, 3, 10), date(2022, 3, 10)), False),
    ((date(2022, 3, 10), date(2022, 3, 10)),
     (date(2022, 1, 1), date(2022, 12, 31)), False),
])
def test_mesadiretora_bordas_de_sobreposicao(existente, nova, aceita):
    legislatura = baker.make(
        'parlamentares.Legislatura',
        data_inicio=date(2021, 1, 1),
        data_fim=date(2024, 12, 31))
    baker.make('parlamentares.MesaDiretora', legislatura=legislatura,
               data_inicio=existente[0], data_fim=existente[1])
    mesa = MesaDiretora(titulo='Nova', legislatura=legislatura,
                        data_inicio=nova[0], data_fim=nova[1])
    if aceita:
        mesa.clean()
    else:
        with pytest.raises(ValidationError, match='se sobrepõem'):
            mesa.clean()


# =====================================================================
# Ordenação padrão de mesas e composições
# =====================================================================

def _cargos_padrao(**ordenacao):
    """Cria Presidente, Vice e Secretário nessa ordem de id."""
    return [baker.make('parlamentares.CargoMesa', descricao=d, unico=True,
                       id_ordenacao=ordenacao.get(chave))
            for chave, d in (('presidente', 'Presidente'),
                             ('vice', 'Vice-Presidente'),
                             ('secretario', 'Secretário'))]


@pytest.mark.django_db(transaction=False)
def test_composicaomesa_ordem_sem_id_ordenacao_segue_id_do_cargo(client):
    presidente, vice, secretario = _cargos_padrao()
    mesa = baker.make('parlamentares.MesaDiretora')
    for cargo, nome in ((secretario, 'Carla Secretária'),
                        (vice, 'Bruno Vice'),
                        (presidente, 'Ana Presidente')):
        baker.make('parlamentares.ComposicaoMesa', mesa_diretora=mesa,
                   cargo=cargo, parlamentar=baker.make(
                       'parlamentares.Parlamentar', nome_parlamentar=nome))

    assert [c.cargo for c in mesa.composicaomesa_set.all()] == \
        [presidente, vice, secretario]

    html = client.get(reverse('sapl.parlamentares:mesadiretora_list'),
                      {'mesa': mesa.pk}).content.decode('utf-8')
    posicoes = [html.index(n) for n in
                ('Ana Presidente', 'Bruno Vice', 'Carla Secretária')]
    assert posicoes == sorted(posicoes)


@pytest.mark.django_db(transaction=False)
def test_composicaomesa_ordem_respeita_id_ordenacao():
    presidente, vice, secretario = _cargos_padrao(
        presidente=2, vice=3, secretario=1)
    mesa = baker.make('parlamentares.MesaDiretora')
    for cargo in (presidente, vice, secretario):
        baker.make('parlamentares.ComposicaoMesa', mesa_diretora=mesa,
                   cargo=cargo)

    assert [c.cargo for c in mesa.composicaomesa_set.all()] == \
        [secretario, presidente, vice]


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_ordem_legislatura_mais_recente_primeiro():
    antiga = baker.make('parlamentares.Legislatura', numero=1,
                        data_inicio=date(2017, 1, 1),
                        data_fim=date(2020, 12, 31))
    nova = baker.make('parlamentares.Legislatura', numero=2,
                      data_inicio=date(2021, 1, 1),
                      data_fim=date(2024, 12, 31))
    m_antiga = baker.make('parlamentares.MesaDiretora', legislatura=antiga,
                          data_inicio=date(2017, 1, 1),
                          data_fim=date(2018, 12, 31))
    m_nova_1 = baker.make('parlamentares.MesaDiretora', legislatura=nova,
                          data_inicio=date(2021, 1, 1),
                          data_fim=date(2022, 12, 31))
    m_nova_2 = baker.make('parlamentares.MesaDiretora', legislatura=nova,
                          data_inicio=date(2023, 1, 1),
                          data_fim=date(2024, 12, 31))

    assert list(MesaDiretora.objects.all()) == [m_nova_2, m_nova_1, m_antiga]


# =====================================================================
# Parâmetros inválidos ou vazios na tela pública
# =====================================================================

@pytest.fixture
def mesas_duas_legislaturas(db):
    antiga = baker.make('parlamentares.Legislatura', numero=1,
                        data_inicio=date(2017, 1, 1),
                        data_fim=date(2020, 12, 31))
    atual = baker.make('parlamentares.Legislatura', numero=2,
                       data_inicio=date(2021, 1, 1),
                       data_fim=date(2024, 12, 31))
    baker.make('parlamentares.MesaDiretora', legislatura=antiga,
               data_inicio=date(2017, 1, 1), data_fim=date(2018, 12, 31))
    baker.make('parlamentares.MesaDiretora', legislatura=atual,
               data_inicio=date(2021, 1, 1), data_fim=date(2022, 12, 31))
    return atual


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('mesa', ['abc', '²', '-1', '9' * 30])
def test_mesadiretora_list_mesa_invalida_retorna_404(
        client, mesas_duas_legislaturas, mesa):
    response = client.get(reverse('sapl.parlamentares:mesadiretora_list'),
                          {'mesa': mesa})
    assert response.status_code == 404


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('params', [{'mesa': ''}, {'legislatura': ''},
                                    {'legislatura': '', 'mesa': ''}])
def test_mesadiretora_list_parametro_vazio_usa_legislatura_atual(
        client, mesas_duas_legislaturas, params):
    response = client.get(reverse('sapl.parlamentares:mesadiretora_list'),
                          params)
    assert response.status_code == 200
    qs = response.context['filter'].qs
    assert qs.count() == 1
    assert qs.first().legislatura == mesas_duas_legislaturas


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_list_select_legislatura_sem_opcao_em_branco(
        client, mesas_duas_legislaturas):
    import re
    html = client.get(
        reverse('sapl.parlamentares:mesadiretora_list')).content.decode()
    select = re.search(r'<select name="legislatura".*?</select>', html,
                       re.S).group(0)
    assert 'value=""' not in select
    assert select.count('<option') == 2


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_list_publica_usa_abas_em_dropdown(
        client, mesas_duas_legislaturas):
    """O estilo de dropdown é opt-in pela classe .nav-tabs--dropdown, para
    não afetar outras telas com .nav-tabs (ex.: subnav da compilação)."""
    html = client.get(
        reverse('sapl.parlamentares:mesadiretora_list')).content.decode()
    assert 'class="nav nav-tabs nav-tabs--dropdown"' in html


# =====================================================================
# Migrations de dados da Mesa Diretora
# =====================================================================

@pytest.mark.django_db(transaction=False)
def test_migration_titulo_nao_repete_o_ano():
    import importlib
    from django.db import connection
    migration = importlib.import_module(
        'sapl.parlamentares.migrations.0049_auto_20260413_1049')
    leg = baker.make('parlamentares.Legislatura',
                     data_inicio=date(2021, 1, 1),
                     data_fim=date(2024, 12, 31))
    um_ano = baker.make(MesaDiretora, legislatura=leg, titulo='',
                        data_inicio=date(2021, 1, 1),
                        data_fim=date(2021, 12, 31))
    vira_o_ano = baker.make(MesaDiretora, legislatura=leg, titulo='',
                            data_inicio=date(2022, 1, 31),
                            data_fim=date(2023, 1, 30))
    bienio = baker.make(MesaDiretora, legislatura=leg, titulo='',
                        data_inicio=date(2023, 2, 1),
                        data_fim=date(2024, 12, 31))

    with connection.schema_editor() as editor:
        migration.preencher_titulo_mesa_diretora(None, editor)

    for mesa in (um_ano, vira_o_ano, bienio):
        mesa.refresh_from_db()
    assert um_ano.titulo == 'Mesa Diretora 2021'
    assert vira_o_ano.titulo == 'Mesa Diretora 2022/2023'
    assert bienio.titulo == 'Mesa Diretora Biênio 2023/2024'


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_list_publica_sem_id_repetido(client):
    mesa = baker.make('parlamentares.MesaDiretora')
    for _i in range(2):
        baker.make('parlamentares.ComposicaoMesa', mesa_diretora=mesa)
    html = client.get(reverse('sapl.parlamentares:mesadiretora_list'),
                      {'mesa': mesa.pk}).content.decode()
    assert 'id="d-flex"' not in html
    assert html.count('class="d-flex align-items-center"') == 2


@pytest.mark.django_db(transaction=False)
def test_migration_registra_mesas_inconsistentes(caplog, capsys):
    import importlib
    from django.apps import apps
    migration = importlib.import_module(
        'sapl.parlamentares.migrations.0053_registra_mesas_inconsistentes')
    leg = baker.make('parlamentares.Legislatura', numero=6,
                     data_inicio=date(1977, 1, 31),
                     data_fim=date(1983, 1, 30))
    fora = baker.make(MesaDiretora, legislatura=leg, titulo='Mesa 1977',
                      data_inicio=date(1977, 1, 1),
                      data_fim=date(1977, 12, 31))
    dup1, dup2 = [baker.make(MesaDiretora, legislatura=leg,
                             data_inicio=date(1979, 1, 1),
                             data_fim=date(1979, 12, 31)) for _i in range(2)]
    ok1 = baker.make(MesaDiretora, legislatura=leg,
                     data_inicio=date(1980, 1, 1),
                     data_fim=date(1980, 12, 31))
    ok2 = baker.make(MesaDiretora, legislatura=leg,  # encosta na ok1
                     data_inicio=date(1980, 12, 31),
                     data_fim=date(1981, 12, 31))

    with caplog.at_level('WARNING'):
        migration.registrar_mesas_inconsistentes(apps, None)

    log = caplog.text
    assert 'Mesa Diretora id={} (Mesa 1977, 01/01/1977 a 31/12/1977): ' \
        'fora do período da legislatura 6 (31/01/1977 a 30/01/1983)'.format(
            fora.id) in log
    assert 'Mesa Diretora id={} ('.format(dup1.id) in log
    assert 'sobrepõe-se à(s) mesa(s) id={}'.format(dup2.id) in log
    for mesa in (ok1, ok2):
        assert 'Mesa Diretora id={} ('.format(mesa.id) not in log
    assert '3 problema(s) em mesas diretoras' in capsys.readouterr().out
    # não altera dados
    fora.refresh_from_db()
    assert fora.data_inicio == date(1977, 1, 1)


@pytest.mark.django_db(transaction=False)
def test_migration_registra_mesas_sem_problemas_nao_imprime(caplog, capsys):
    import importlib
    from django.apps import apps
    migration = importlib.import_module(
        'sapl.parlamentares.migrations.0053_registra_mesas_inconsistentes')
    baker.make(MesaDiretora,
               legislatura=baker.make('parlamentares.Legislatura',
                                      data_inicio=date(2021, 1, 1),
                                      data_fim=date(2024, 12, 31)),
               data_inicio=date(2021, 1, 1), data_fim=date(2022, 12, 31))
    with caplog.at_level('WARNING'):
        migration.registrar_mesas_inconsistentes(apps, None)
    assert caplog.text == ''
    assert capsys.readouterr().out == ''


# =====================================================================
# Upgrade a partir do modelo antigo (MesaDiretora ligada à sessão)
# =====================================================================

ANTES_DA_MESA = [('parlamentares', '0046_parlamentar_data_ultima_atualizacao')]
MIGRATION_0047 = [('parlamentares', '0047_mesadiretora_legislatura')]


def _migrar(alvo):
    """Migra o app para o estado `alvo` e devolve os models históricos."""
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    executor = MigrationExecutor(connection)
    executor.migrate(alvo)
    return MigrationExecutor(connection).loader.project_state(alvo).apps


def _folhas_parlamentares():
    from django.db import connection
    from django.db.migrations.loader import MigrationLoader
    return [n for n in MigrationLoader(connection).graph.leaf_nodes()
            if n[0] == 'parlamentares']


@pytest.fixture
def estado_antigo():
    """Volta parlamentares para antes da refatoração da Mesa Diretora e,
    ao final, reaplica todas as migrations.

    Os testes que o usam precisam de django_db(transaction=True,
    serialized_rollback=True): a migração faz DDL, e sem o
    serialized_rollback o flush do teardown dispara os post_migrate do SAPL,
    que falham ao recriar permissões (vale para qualquer teste transacional).
    """
    ultima = _folhas_parlamentares()
    try:
        yield _migrar(ANTES_DA_MESA)
    finally:
        _migrar(ultima)


def _sessao_antiga(apps):
    legislatura = baker.make(apps.get_model('parlamentares', 'Legislatura'),
                             data_inicio=date(2025, 1, 1),
                             data_fim=date(2028, 12, 31))
    return baker.make(apps.get_model('parlamentares', 'SessaoLegislativa'),
                      legislatura=legislatura,
                      data_inicio=date(2025, 12, 23),
                      data_fim=date(2026, 12, 21))


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_migration_0047_preserva_datas_proprias_da_mesa(estado_antigo):
    Mesa = estado_antigo.get_model('parlamentares', 'MesaDiretora')
    sessao = _sessao_antiga(estado_antigo)
    semestre1 = Mesa.objects.create(sessao_legislativa=sessao,
                                    data_inicio=date(2026, 1, 1),
                                    data_fim=date(2026, 6, 30))
    semestre2 = Mesa.objects.create(sessao_legislativa=sessao,
                                    data_inicio=date(2026, 7, 1),
                                    data_fim=date(2026, 12, 21))
    sem_datas = Mesa.objects.create(sessao_legislativa=sessao)

    apps = _migrar(MIGRATION_0047)
    Mesa = apps.get_model('parlamentares', 'MesaDiretora')

    def periodo(mesa):
        m = Mesa.objects.get(pk=mesa.pk)
        return m.data_inicio, m.data_fim, m.legislatura_id

    leg = sessao.legislatura_id
    assert periodo(semestre1) == (date(2026, 1, 1), date(2026, 6, 30), leg)
    assert periodo(semestre2) == (date(2026, 7, 1), date(2026, 12, 21), leg)
    assert periodo(sem_datas) == (date(2025, 12, 23), date(2026, 12, 21), leg)


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_migration_0047_remove_composicao_sem_mesa(estado_antigo, capsys):
    Mesa = estado_antigo.get_model('parlamentares', 'MesaDiretora')
    Composicao = estado_antigo.get_model('parlamentares', 'ComposicaoMesa')
    mesa = Mesa.objects.create(sessao_legislativa=_sessao_antiga(
        estado_antigo))
    parlamentar = baker.make(
        estado_antigo.get_model('parlamentares', 'Parlamentar'),
        nome_parlamentar='Fulano Órfão')
    cargo = baker.make(estado_antigo.get_model('parlamentares', 'CargoMesa'),
                       descricao='Presidente')
    com_mesa = Composicao.objects.create(mesa_diretora=mesa, cargo=cargo,
                                         parlamentar=parlamentar)
    orfa = Composicao.objects.create(mesa_diretora=None, cargo=cargo,
                                     parlamentar=parlamentar)

    apps = _migrar(MIGRATION_0047)
    Composicao = apps.get_model('parlamentares', 'ComposicaoMesa')

    assert list(Composicao.objects.values_list('id', flat=True)) == \
        [com_mesa.pk]
    saida = capsys.readouterr().out
    assert 'ComposicaoMesa id={} (Fulano Órfão - Presidente)'.format(
        orfa.pk) in saida
    assert '1 ocupação(ões) de cargo na Mesa sem mesa diretora' in saida


@pytest.mark.django_db(transaction=False)
def test_migration_0048_reversao_com_mesas_da_erro_claro():
    import importlib
    from django.apps import apps
    from django.db.migrations.exceptions import IrreversibleError
    migration = importlib.import_module(
        'sapl.parlamentares.migrations.0048_auto_20260412_2256')

    migration.impede_reversao_com_mesas(apps, None)  # base sem mesas: ok

    baker.make(MesaDiretora)
    with pytest.raises(IrreversibleError, match='Restaure o backup'):
        migration.impede_reversao_com_mesas(apps, None)


@pytest.mark.django_db(transaction=False)
def test_composicaomesa_create_mesa_inexistente_retorna_404(admin_client):
    response = admin_client.get(reverse(
        'sapl.parlamentares:composicaomesa_create', kwargs={'pk': 999999}))
    assert response.status_code == 404


@pytest.mark.django_db(transaction=False)
@pytest.mark.parametrize('legislatura', ['abc', '²', '999999'])
def test_mesadiretora_list_legislatura_invalida_retorna_404(
        client, mesas_duas_legislaturas, legislatura):
    response = client.get(reverse('sapl.parlamentares:mesadiretora_list'),
                          {'legislatura': legislatura})
    assert response.status_code == 404


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_list_legislatura_sem_mesas_avisa(client):
    """Ex.: início de uma legislatura nova, antes de a mesa ser cadastrada."""
    nova = baker.make('parlamentares.Legislatura',
                      data_inicio=date(2025, 1, 1),
                      data_fim=date(2028, 12, 31))
    response = client.get(reverse('sapl.parlamentares:mesadiretora_list'),
                          {'legislatura': nova.pk})
    html = response.content.decode()
    assert response.status_code == 200
    assert 'Nenhuma Mesa Diretora cadastrada para esta legislatura.' in html
    assert 'class="nav nav-tabs nav-tabs--dropdown"' not in html


def _abas_ativas(html):
    import re
    abas = re.findall(r'class="nav-link active" id="tab-mesa-(\d+)-tab"', html)
    paineis = re.findall(r'tab-pane fade show active" id="tab-mesa-(\d+)"',
                         html)
    return abas, paineis


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_list_aba_ativa(client):
    leg_a = baker.make('parlamentares.Legislatura',
                       data_inicio=date(2017, 1, 1),
                       data_fim=date(2020, 12, 31))
    leg_b = baker.make('parlamentares.Legislatura',
                       data_inicio=date(2021, 1, 1),
                       data_fim=date(2024, 12, 31))
    outra = baker.make('parlamentares.MesaDiretora', legislatura=leg_a,
                       data_inicio=date(2017, 1, 1),
                       data_fim=date(2018, 12, 31))
    antiga = baker.make('parlamentares.MesaDiretora', legislatura=leg_b,
                        data_inicio=date(2021, 1, 1),
                        data_fim=date(2022, 12, 31))
    recente = baker.make('parlamentares.MesaDiretora', legislatura=leg_b,
                         data_inicio=date(2023, 1, 1),
                         data_fim=date(2024, 12, 31))
    url = reverse('sapl.parlamentares:mesadiretora_list')

    def ativas(params):
        return _abas_ativas(client.get(url, params).content.decode())

    # sem ?mesa=: a primeira (mais recente)
    assert ativas({'legislatura': leg_b.pk}) == ([str(recente.pk)],
                                                 [str(recente.pk)])
    # ?mesa= da própria legislatura
    assert ativas({'mesa': antiga.pk}) == ([str(antiga.pk)],
                                           [str(antiga.pk)])
    # ?mesa= de outra legislatura: antes nenhuma aba ficava ativa
    assert ativas({'legislatura': leg_b.pk, 'mesa': outra.pk}) == (
        [str(recente.pk)], [str(recente.pk)])


@pytest.mark.django_db(transaction=False)
def test_mesadiretora_list_queries_nao_crescem_com_as_mesas(client):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    def legislatura_com(n_mesas, ano):
        leg = baker.make('parlamentares.Legislatura',
                         data_inicio=date(ano, 1, 1),
                         data_fim=date(ano + 3, 12, 31))
        for i in range(n_mesas):
            mesa = baker.make('parlamentares.MesaDiretora', legislatura=leg,
                              titulo='Mesa {}'.format(i),
                              data_inicio=date(ano + i, 1, 1),
                              data_fim=date(ano + i, 12, 31))
            baker.make('parlamentares.ComposicaoMesa', mesa_diretora=mesa,
                       _quantity=2)
        return leg

    url = reverse('sapl.parlamentares:mesadiretora_list')
    pequena, grande = legislatura_com(1, 2013), legislatura_com(4, 2017)

    def queries(leg):
        client.get(url, {'legislatura': leg.pk})  # aquece caches
        with CaptureQueriesContext(connection) as ctx:
            client.get(url, {'legislatura': leg.pk})
        return len(ctx.captured_queries)

    assert queries(pequena) == queries(grande)
