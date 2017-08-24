import pytest
from model_mommy import mommy

from sapl.compilacao import forms
from sapl.compilacao.models import PerfilEstruturalTextoArticulado


def test_valida_campos_obrigatorios_tipo_texto_articulado_form():
    form = forms.TipoTaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['sigla'] == ['Este campo é obrigatório.']
    assert errors['descricao'] == ['Este campo é obrigatório.']
    assert errors['content_type'] == ['Este campo é obrigatório.']
    assert errors['participacao_social'] == ['Este campo é obrigatório.']
    assert errors['publicacao_func'] == ['Este campo é obrigatório.']

    assert len(errors) == 5


@pytest.mark.django_db(transaction=False)
def test_tipo_texto_articulado_form_valid():
    perfil = mommy.make(PerfilEstruturalTextoArticulado)

    form = forms.TipoTaForm(data={'sigla': 'si',
                                  'descricao': 'teste',
                                  'content_type': 'content',
                                  'participacao_social': 'social',
                                  'publicacao_func': 'func',
                                  'perfis': str(perfil.pk)
                                  })

    assert form.is_valid()
