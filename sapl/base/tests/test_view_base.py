import pytest
from model_mommy import mommy
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from sapl.base.views import (protocolos_duplicados, protocolos_com_materias,
                             materias_protocolo_inexistente)
from sapl.protocoloadm.models import Protocolo
from sapl.materia.models import (TipoMateriaLegislativa, RegimeTramitacao,
                                 MateriaLegislativa)        


@pytest.mark.django_db(transaction=False)
def test_lista_protocolos_duplicados():
        protocolo_a = mommy.make(
                Protocolo,
                numero=15,
                ano=2031
        )
        protocolo_b = mommy.make(
                Protocolo,
                numero=15,
                ano=2031
        )
        protocolo_c = mommy.make(
                Protocolo,
                numero=33,
                ano=2033
        )

        lista_protocolos_duplicados = protocolos_duplicados()
        
        assert len(lista_protocolos_duplicados) == 1
        assert lista_protocolos_duplicados[0][1] == 2
        assert lista_protocolos_duplicados[0][0].numero == 15
        assert lista_protocolos_duplicados[0][0].ano == 2031


@pytest.mark.django_db(transaction=False)
def test_lista_protocolos_com_materias():
        protocolo_a = mommy.make(
                Protocolo,
                numero=15,
                ano=2035
        )
        protocolo_b = mommy.make(
                Protocolo,
                numero=33,
                ano=2035
        )
        
        tipo_materia = mommy.make(
                TipoMateriaLegislativa,
                descricao="Tipo_Teste"
        )
        regime_tramitacao = mommy.make(
                RegimeTramitacao,
                descricao="Regime_Teste"
        )
        materia_a = mommy.make(
                MateriaLegislativa,
                numero=16,
                ano=2035,
                data_apresentacao='2035-06-02',
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia,
                numero_protocolo=15
        )
        materia_b = mommy.make(
                MateriaLegislativa,
                numero=17,
                ano=2035,
                data_apresentacao='2035-06-05',
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia,
                numero_protocolo=15
        )

        lista_protocolos_com_materias = protocolos_com_materias()
        
        assert len(lista_protocolos_com_materias) == 1
        assert lista_protocolos_com_materias[0][1] == 2
        assert lista_protocolos_com_materias[0][0].numero_protocolo == 15
        assert lista_protocolos_com_materias[0][0].ano == 2035


@pytest.mark.django_db(transaction=False)
def test_lista_materias_protocolo_inexistente():
        protocolo_a = mommy.make(
                Protocolo,
                numero=15,
                ano=2031
        )

        tipo_materia = mommy.make(
                TipoMateriaLegislativa,
                descricao="Tipo_Teste"
        )
        regime_tramitacao = mommy.make(
                RegimeTramitacao,
                descricao="Regime_Teste"
        )
        materia_a = mommy.make(
                MateriaLegislativa,
                numero=16,
                ano=2031,
                data_apresentacao='2031-06-02',
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia,
                numero_protocolo=15
        )
        materia_b = mommy.make(
                MateriaLegislativa,
                numero=17,
                ano=2031,
                data_apresentacao='2031-06-02',
                regime_tramitacao=regime_tramitacao,
                tipo=tipo_materia,
                numero_protocolo=16
        )

        lista_materias_protocolo_inexistente = materias_protocolo_inexistente()

        assert len(lista_materias_protocolo_inexistente) == 1
        assert lista_materias_protocolo_inexistente[0][2] == 16
        assert lista_materias_protocolo_inexistente[0][1] == 2031
        assert lista_materias_protocolo_inexistente[0][0] == materia_b        


@pytest.mark.django_db(transaction=False)
def test_incluir_casa_legislativa_errors(admin_client):

    response = admin_client.post(reverse('sapl.base:casalegislativa_create'),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['nome'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['sigla'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['endereco'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['cep'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['municipio'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['uf'] ==
            [_('Este campo é obrigatório.')])


@pytest.mark.django_db(transaction=False)
def test_incluir_tipo_autor_errors(admin_client):

    response = admin_client.post(reverse('sapl.base:tipoautor_create'),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['descricao'] ==
            [_('Este campo é obrigatório.')])
