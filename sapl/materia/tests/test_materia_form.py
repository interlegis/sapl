import pytest
from django.utils.translation import ugettext as _
from model_mommy import mommy

from sapl.materia import forms
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_ficha_pesquisa_form():
    form = forms.FichaPesquisaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['tipo_materia'] == [_('Este campo é obrigatório.')]
    assert errors['data_inicial'] == [_('Este campo é obrigatório.')]
    assert errors['data_final'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 3


@pytest.mark.django_db(transaction=False)
def test_ficha_pesquisa_form_datas_invalidas():
    tipo = mommy.make(TipoMateriaLegislativa)

    form = forms.FichaPesquisaForm(data={'tipo_materia': str(tipo.pk),
                                         'data_inicial': '10/11/2017',
                                         'data_final': '09/11/2017'
                                         })
    assert not form.is_valid()
    assert form.errors['__all__'] == [_('A Data Final não pode ser menor que '
                                        'a Data Inicial')]


@pytest.mark.django_db(transaction=False)
def test_ficha_pesquisa_form_invalido():
    tipo = mommy.make(TipoMateriaLegislativa)

    form = forms.FichaPesquisaForm(data={'tipo_materia': str(tipo.pk),
                                         'data_inicial': '10/11/2017',
                                         'data_final': '09/11/2017'
                                         })

    assert not form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_ficha_seleciona_form():
    form = forms.FichaSelecionaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['materia'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 1


@pytest.mark.django_db(transaction=False)
def test_ficha_seleciona_form_valido():
    materia = mommy.make(MateriaLegislativa)

    form = forms.FichaSelecionaForm(data={'materia': str(materia.pk)})

    assert form.is_valid()
