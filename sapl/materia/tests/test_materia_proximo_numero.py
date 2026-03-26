from datetime import date

import pytest
from django.db import IntegrityError, transaction
from model_bakery import baker
from rest_framework.test import APIClient

from sapl.base.models import AppConfig as BaseAppConfig
from sapl.materia.models import (MateriaLegislativa, RegimeTramitacao,
                                 TipoMateriaLegislativa)
from sapl.parlamentares.models import Legislatura


# ---------------------------------------------------------------------------
#  Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tipo_materia(db):
    """TipoMateriaLegislativa sem sequencia_numeracao própria (usa global)."""
    return baker.make(TipoMateriaLegislativa, descricao='Projeto de Lei',
                      sigla='PL', sequencia_numeracao='')


@pytest.fixture
def tipo_materia_anual(db):
    return baker.make(TipoMateriaLegislativa, descricao='Requerimento',
                      sigla='REQ', sequencia_numeracao='A')


@pytest.fixture
def tipo_materia_unico(db):
    return baker.make(TipoMateriaLegislativa, descricao='Indicação',
                      sigla='IND', sequencia_numeracao='U')


@pytest.fixture
def tipo_materia_legislatura(db):
    return baker.make(TipoMateriaLegislativa, descricao='PEC',
                      sigla='PEC', sequencia_numeracao='L')


@pytest.fixture
def regime(db):
    return baker.make(RegimeTramitacao, descricao='Normal')


@pytest.fixture
def app_config(db):
    return BaseAppConfig.objects.create(sequencia_numeracao_protocolo='A')


def _criar_materia(tipo, numero, ano, regime, **kwargs):
    """Atalho para criar MateriaLegislativa com campos obrigatórios."""
    defaults = dict(
        tipo=tipo,
        numero=numero,
        ano=ano,
        data_apresentacao=date(ano, 1, 1),
        regime_tramitacao=regime,
        ementa='Ementa de teste',
    )
    defaults.update(kwargs)
    return MateriaLegislativa.objects.create(**defaults)


# ===========================================================================
#  Testes de get_proximo_numero – numeração por ano (padrão)
# ===========================================================================

@pytest.mark.django_db(transaction=False)
def test_proximo_numero_primeiro_do_ano(tipo_materia_anual, regime, app_config):
    """Sem matérias existentes, o primeiro número gerado deve ser 1."""
    with transaction.atomic():
        numero, ano = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_anual, ano=2024)
    assert numero == 1
    assert ano == 2024


@pytest.mark.django_db(transaction=False)
def test_proximo_numero_sequencial(tipo_materia_anual, regime, app_config):
    """Com matérias existentes 1, 2, 3 → próximo deve ser 4."""
    for n in (1, 2, 3):
        _criar_materia(tipo_materia_anual, n, 2024, regime)

    with transaction.atomic():
        numero, ano = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_anual, ano=2024)
    assert numero == 4
    assert ano == 2024


@pytest.mark.django_db(transaction=False)
def test_proximo_numero_ignora_outro_ano(tipo_materia_anual, regime, app_config):
    """Matérias em anos diferentes não influenciam a sequência."""
    _criar_materia(tipo_materia_anual, 10, 2023, regime,
                   data_apresentacao=date(2023, 6, 1))
    _criar_materia(tipo_materia_anual, 1, 2024, regime)

    with transaction.atomic():
        numero, ano = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_anual, ano=2024)
    assert numero == 2


@pytest.mark.django_db(transaction=False)
def test_proximo_numero_ignora_outro_tipo(tipo_materia_anual, regime, app_config):
    """Matérias de outro tipo não influenciam a sequência."""
    outro_tipo = baker.make(TipoMateriaLegislativa, descricao='Moção',
                            sigla='MOC', sequencia_numeracao='A')
    _criar_materia(outro_tipo, 50, 2024, regime)
    _criar_materia(tipo_materia_anual, 3, 2024, regime)

    with transaction.atomic():
        numero, _ = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_anual, ano=2024)
    assert numero == 4


# ===========================================================================
#  Testes de get_proximo_numero – numeração única
# ===========================================================================

@pytest.mark.django_db(transaction=False)
def test_proximo_numero_unico(tipo_materia_unico, regime, app_config):
    """Numeração 'U' ignora o ano – sequência é global por tipo."""
    _criar_materia(tipo_materia_unico, 1, 2022, regime,
                   data_apresentacao=date(2022, 1, 1))
    _criar_materia(tipo_materia_unico, 2, 2023, regime,
                   data_apresentacao=date(2023, 1, 1))

    with transaction.atomic():
        numero, _ = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_unico, ano=2024)
    assert numero == 3


# ===========================================================================
#  Testes de get_proximo_numero – numeração por legislatura
# ===========================================================================

@pytest.mark.django_db(transaction=False)
def test_proximo_numero_por_legislatura(tipo_materia_legislatura, regime,
                                        app_config):
    """Numeração 'L' conta apenas matérias dentro da legislatura vigente."""
    baker.make(Legislatura, numero=1,
               data_inicio=date(2021, 1, 1),
               data_fim=date(2024, 12, 31),
               data_eleicao=date(2020, 11, 15))

    _criar_materia(tipo_materia_legislatura, 1, 2022, regime,
                   data_apresentacao=date(2022, 3, 1))
    _criar_materia(tipo_materia_legislatura, 2, 2023, regime,
                   data_apresentacao=date(2023, 5, 1))

    with transaction.atomic():
        numero, _ = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_legislatura, ano=2024)
    assert numero == 3


@pytest.mark.django_db(transaction=False)
def test_proximo_numero_legislatura_inexistente(tipo_materia_legislatura,
                                                 regime, app_config):
    """Sem legislatura vigente, número inicia em 1."""
    with transaction.atomic():
        numero, _ = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_legislatura, ano=2050)
    assert numero == 1


# ===========================================================================
#  Testes de get_proximo_numero – numero_candidato
# ===========================================================================

@pytest.mark.django_db(transaction=False)
def test_numero_candidato_disponivel(tipo_materia_anual, regime, app_config):
    """Se o número candidato está disponível, deve ser retornado."""
    _criar_materia(tipo_materia_anual, 1, 2024, regime)

    with transaction.atomic():
        numero, _ = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_anual, ano=2024, numero_candidato=5)
    assert numero == 5


@pytest.mark.django_db(transaction=False)
def test_numero_candidato_em_uso_retorna_sequencial(tipo_materia_anual,
                                                     regime, app_config):
    """Se o número candidato já existe, retorna o sequencial."""
    _criar_materia(tipo_materia_anual, 5, 2024, regime)

    with transaction.atomic():
        numero, _ = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_anual, ano=2024, numero_candidato=5)
    assert numero == 6


# ===========================================================================
#  Testes de get_proximo_numero – resolução de tipo por pk (int/str)
# ===========================================================================

@pytest.mark.django_db(transaction=False)
def test_tipo_passado_como_int(tipo_materia_anual, app_config):
    """O tipo pode ser passado como int (pk)."""
    with transaction.atomic():
        numero, _ = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_anual.pk, ano=2024)
    assert numero == 1


@pytest.mark.django_db(transaction=False)
def test_tipo_passado_como_str(tipo_materia_anual, app_config):
    """O tipo pode ser passado como str representando o pk."""
    with transaction.atomic():
        numero, _ = MateriaLegislativa.get_proximo_numero(
            tipo=str(tipo_materia_anual.pk), ano=2024)
    assert numero == 1


@pytest.mark.django_db(transaction=False)
def test_tipo_inexistente_levanta_excecao(app_config):
    """Pk inexistente deve levantar DoesNotExist."""
    with pytest.raises(TipoMateriaLegislativa.DoesNotExist):
        with transaction.atomic():
            MateriaLegislativa.get_proximo_numero(tipo=99999, ano=2024)


@pytest.mark.django_db(transaction=False)
def test_tipo_invalido_levanta_validation_error(app_config):
    """Tipo não conversível para int deve levantar ValidationError."""
    from django.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        with transaction.atomic():
            MateriaLegislativa.get_proximo_numero(tipo='abc', ano=2024)


# ===========================================================================
#  Testes de get_proximo_numero – ano padrão
# ===========================================================================

@pytest.mark.django_db(transaction=False)
def test_ano_none_usa_ano_atual(tipo_materia_anual, app_config):
    """Se ano=None, deve usar o ano corrente."""
    from django.utils import timezone
    with transaction.atomic():
        _, ano = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia_anual, ano=None)
    assert ano == timezone.now().year


# ===========================================================================
#  Testes de get_proximo_numero – select_for_update (proteção concorrência)
# ===========================================================================

@pytest.mark.django_db(transaction=False)
def test_unique_together_protege_duplicata(tipo_materia_anual, regime,
                                           app_config):
    """O unique_together (tipo, numero, ano) impede duplicatas no banco."""
    _criar_materia(tipo_materia_anual, 1, 2024, regime)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            _criar_materia(tipo_materia_anual, 1, 2024, regime)


# ===========================================================================
#  Testes de global config – tipo sem sequencia_numeracao usa global
# ===========================================================================

@pytest.mark.django_db(transaction=False)
def test_tipo_sem_sequencia_usa_config_global(tipo_materia, regime, app_config):
    """Tipo com sequencia_numeracao vazio deve usar a config global ('A')."""
    _criar_materia(tipo_materia, 1, 2024, regime)
    _criar_materia(tipo_materia, 2, 2024, regime)
    _criar_materia(tipo_materia, 10, 2023, regime,
                   data_apresentacao=date(2023, 1, 1))

    with transaction.atomic():
        numero, _ = MateriaLegislativa.get_proximo_numero(
            tipo=tipo_materia, ano=2024)
    # global default 'A' → sequencial por ano → MAX(2024) = 2 → próximo = 3
    assert numero == 3


# ===========================================================================
#  Testes do endpoint API create (MateriaLegislativaViewSet)
# ===========================================================================

@pytest.fixture
def api_client_autenticado(db):
    """APIClient autenticado como superusuário (tem todas as permissões)."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_superuser(
        username='admin_api', password='secret123', email='a@b.com')
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db(transaction=False)
def test_api_create_sem_numero_auto_gera(api_client_autenticado,
                                          tipo_materia_anual, regime,
                                          app_config):
    """POST sem 'numero' deve auto-gerar próximo sequencial."""
    _criar_materia(tipo_materia_anual, 1, 2024, regime)

    response = api_client_autenticado.post(
        '/api/materia/materialegislativa/',
        {
            'tipo': tipo_materia_anual.pk,
            'ano': 2024,
            'data_apresentacao': '2024-06-01',
            'regime_tramitacao': regime.pk,
            'ementa': 'Teste auto-gerar número',
        },
        format='json',
    )
    assert response.status_code == 201
    assert response.data['numero'] == 2


@pytest.mark.django_db(transaction=False)
def test_api_create_com_numero_respeita_dado(api_client_autenticado,
                                              tipo_materia_anual, regime,
                                              app_config):
    """POST com 'numero' explícito deve criar com o número informado."""
    response = api_client_autenticado.post(
        '/api/materia/materialegislativa/',
        {
            'tipo': tipo_materia_anual.pk,
            'numero': 42,
            'ano': 2024,
            'data_apresentacao': '2024-06-01',
            'regime_tramitacao': regime.pk,
            'ementa': 'Número exato',
        },
        format='json',
    )
    assert response.status_code == 201
    assert response.data['numero'] == 42


@pytest.mark.django_db(transaction=False)
def test_api_create_numero_duplicado_retorna_erro(api_client_autenticado,
                                                   tipo_materia_anual, regime,
                                                   app_config):
    """POST com número já existente retorna erro.

    O DRF detecta a violação de unique_together via UniqueTogetherValidator
    no serializer e retorna 400 antes de chegar ao banco.
    """
    _criar_materia(tipo_materia_anual, 42, 2024, regime)

    response = api_client_autenticado.post(
        '/api/materia/materialegislativa/',
        {
            'tipo': tipo_materia_anual.pk,
            'numero': 42,
            'ano': 2024,
            'data_apresentacao': '2024-06-01',
            'regime_tramitacao': regime.pk,
            'ementa': 'Duplicata',
        },
        format='json',
    )
    assert response.status_code == 400


@pytest.mark.django_db(transaction=False)
def test_api_create_sem_tipo_valida_serializer(api_client_autenticado, regime):
    """POST sem 'tipo' deve falhar na validação do serializer (400)."""
    response = api_client_autenticado.post(
        '/api/materia/materialegislativa/',
        {
            'numero': 1,
            'ano': 2024,
            'data_apresentacao': '2024-06-01',
            'regime_tramitacao': regime.pk,
            'ementa': 'Sem tipo',
        },
        format='json',
    )
    assert response.status_code == 400
