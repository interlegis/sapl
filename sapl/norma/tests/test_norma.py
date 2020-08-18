from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from model_bakery import baker
import pytest

from sapl.base.models import AppConfig
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.norma.forms import (NormaJuridicaForm, NormaPesquisaSimplesForm,
                              NormaRelacionadaForm)
from sapl.norma.models import NormaJuridica, TipoNormaJuridica


@pytest.mark.django_db(transaction=False)
def test_incluir_norma_submit(admin_client):
    # Cria um tipo de norma
    tipo = baker.make(TipoNormaJuridica,
                      sigla='T',
                      descricao='Teste')
    config = baker.make(AppConfig)

    # Testa POST
    response = admin_client.post(reverse('sapl.norma:normajuridica_create'),
                                 {'tipo': tipo.pk,
                                  'numero': '1',
                                  'ano': '2016',
                                  'data': '2016-03-22',
                                  'esfera_federacao': 'E',
                                  'ementa': 'Teste_Ementa',
                                  'salvar': 'salvar'},
                                 follow=True)
    assert response.status_code == 200

    norma = NormaJuridica.objects.first()
    assert norma.numero == '1'
    assert norma.ano == 2016
    assert norma.tipo == tipo


@pytest.mark.django_db(transaction=False)
def test_incluir_norma_errors(admin_client):

    response = admin_client.post(reverse('sapl.norma:normajuridica_create'),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['tipo'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['numero'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['ano'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['data'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['esfera_federacao'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['ementa'] ==
            [_('Este campo é obrigatório.')])


# TODO esse teste repete o teste acima (test_incluir_norma_errors)
# mas a granularidade certa para testar campos obrigatórios seria
# no nível de form ou então de model, não de client...
def test_norma_form_invalida():
    form = NormaJuridicaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['numero'] == [_('Este campo é obrigatório.')]
    assert errors['ano'] == [_('Este campo é obrigatório.')]
    assert errors['data'] == [_('Este campo é obrigatório.')]
    assert errors['esfera_federacao'] == [_('Este campo é obrigatório.')]
    assert errors['ementa'] == [_('Este campo é obrigatório.')]


@pytest.mark.django_db(transaction=False)
def test_norma_juridica_materia_inexistente():

    tipo = baker.make(TipoNormaJuridica)
    tipo_materia = baker.make(TipoMateriaLegislativa, descricao='VETO')

    # cria uma matéria qualquer em 2017 pois, no teste, o campo ano_materia
    # está vazio
    materia = baker.make(MateriaLegislativa,
                         tipo=tipo_materia,
                         ano=2017,
                         numero=1,
                         data_apresentacao='2017-03-05'
                         )

    form = NormaJuridicaForm(data={'tipo': str(tipo.pk),
                                   'numero': '1',
                                   'ano': '2017',
                                   'data': '2017-12-12',
                                   'esfera_federacao': 'F',
                                   'ementa': 'teste norma',
                                   'tipo_materia': str(tipo_materia.pk),
                                   'numero_materia': '2',
                                   'ano_materia': '2017'
                                   })

    assert not form.is_valid()

    assert form.errors['__all__'] == [
        _("Matéria Legislativa 2/2017 (VETO) é inexistente.")]


@pytest.mark.django_db(transaction=False)
def test_norma_juridica_materia_existente():
    tipo = baker.make(TipoNormaJuridica)
    tipo_materia = baker.make(TipoMateriaLegislativa)
    baker.make(MateriaLegislativa,
               numero=2,
               ano=2017,
               tipo=tipo_materia)

    form = NormaJuridicaForm(data={'tipo': str(tipo.pk),
                                   'numero': '1',
                                   'ano': '2017',
                                   'data': '2017-12-12',
                                   'esfera_federacao': 'F',
                                   'ementa': 'teste norma',
                                   'tipo_materia': str(tipo_materia.pk),
                                   'numero_materia': '2',
                                   'ano_materia': '2017'
                                   })
    assert form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_norma_relacionada_form_campos_obrigatorios():
    form = NormaRelacionadaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['numero'] == [_('Este campo é obrigatório.')]
    assert errors['ano'] == [_('Este campo é obrigatório.')]
    assert errors['tipo_vinculo'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 4


@pytest.mark.django_db(transaction=False)
def test_norma_pesquisa_form_datas_invalidas():
    tipo = baker.make(TipoNormaJuridica)

    form = NormaPesquisaSimplesForm(data={'tipo_norma': str(tipo.pk),
                                          'data_inicial': '10/11/2017',
                                          'data_final': '09/11/2017'
                                          })
    assert not form.is_valid()
    assert form.errors['__all__'] == [_('A Data Final não pode ser menor que '
                                        'a Data Inicial')]
