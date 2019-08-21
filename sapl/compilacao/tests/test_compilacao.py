import pytest
from model_mommy import mommy

from sapl.compilacao.models import PerfilEstruturalTextoArticulado
from sapl.compilacao.models import TipoTextoArticulado
from sapl.compilacao.models import TextoArticulado, TipoNota
from sapl.compilacao.models import TipoVide, TipoDispositivo
from sapl.compilacao.models import TipoDispositivoRelationship


@pytest.mark.django_db(transaction=False)
def test_perfil_estrutural_texto_articulado_model():
    perfil_estrutural_texto_articulado = mommy.make(
        PerfilEstruturalTextoArticulado,
        nome='Teste_Nome_Perfil',
        sigla='TSPETA')

    assert perfil_estrutural_texto_articulado.nome == 'Teste_Nome_Perfil'
    assert perfil_estrutural_texto_articulado.sigla == 'TSPETA'


@pytest.mark.django_db(transaction=False)
def test_tipo_texto_articulado_model():
    tipo_texto_articulado = mommy.make(
        TipoTextoArticulado,
        sigla='TTP',
        descricao='T_Desc_Tipo_Texto_Articulado'
    )

    assert tipo_texto_articulado.sigla == 'TTP'
    assert tipo_texto_articulado.descricao == 'T_Desc_Tipo_Texto_Articulado'


@pytest.mark.django_db(transaction=False)
def test_texto_articulado_model():
    texto_articulado = mommy.make(
        TextoArticulado,
        ementa='Teste_Ementa_Texto_Articulado',
        numero='12345678',
        ano=2016,
    )

    assert texto_articulado.ementa == 'Teste_Ementa_Texto_Articulado'
    assert texto_articulado.numero == '12345678'
    assert texto_articulado.ano == 2016


@pytest.mark.django_db(transaction=False)
def test_tipo_nota_model():
    tipo_nota = mommy.make(
        TipoNota,
        sigla='TTN',
        nome='Teste_Nome_Tipo_Nota'
    )

    assert tipo_nota.sigla == 'TTN'
    assert tipo_nota.nome == 'Teste_Nome_Tipo_Nota'


@pytest.mark.django_db(transaction=False)
def test_tipo_vide_model():
    tipo_vide = mommy.make(
        TipoVide,
        sigla='TTV',
        nome='Teste_Nome_Tipo_Vide'
    )

    assert tipo_vide.sigla == 'TTV'
    assert tipo_vide.nome == 'Teste_Nome_Tipo_Vide'


@pytest.mark.django_db(transaction=False)
def test_tipo_dispositivo_model():
    tipo_dispositivo = mommy.make(
        TipoDispositivo,
        nome='Teste_Nome_Tipo_Dispositivo',
        rotulo_ordinal=0
    )

    assert tipo_dispositivo.nome == 'Teste_Nome_Tipo_Dispositivo'
    assert tipo_dispositivo.rotulo_ordinal == 0


@pytest.mark.django_db(transaction=False)
def test_tipo_dispositivo_relationship_model():
    tipo_dispositivo_pai = mommy.make(
        TipoDispositivo,
        nome='Tipo_Dispositivo_Pai',
        rotulo_ordinal=0
    )

    t_dispositivo_filho = mommy.make(
        TipoDispositivo,
        nome='Tipo_Dispositivo_Filho',
        rotulo_ordinal=0
    )

    p_e_texto_articulado = mommy.make(
        PerfilEstruturalTextoArticulado,
        nome='Teste_Nome_Perfil',
        sigla='TSPETA')

    tipo_dispositivo_relationship = mommy.make(
        TipoDispositivoRelationship,
        pai=tipo_dispositivo_pai,
        filho_permitido=t_dispositivo_filho,
        perfil=p_e_texto_articulado,
    )

    assert tipo_dispositivo_relationship.pai == tipo_dispositivo_pai
    assert tipo_dispositivo_relationship.perfil == p_e_texto_articulado
    assert tipo_dispositivo_relationship.filho_permitido == t_dispositivo_filho
