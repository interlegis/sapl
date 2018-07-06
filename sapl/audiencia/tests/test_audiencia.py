import pytest
from django.utils.translation import ugettext as _
from model_mommy import mommy

from sapl.audiencia import forms

@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_audiencia_form():
    form = forms.AudienciaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['nome'] == [_('Este campo é obrigatório.')]
    assert errors['tema'] == [_('Este campo é obrigatório.')]
    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['tipo_materia'] == [_('Este campo é obrigatório.')]
    assert errors['numero_materia'] == [_('Este campo é obrigatório.')]
    assert errors['ano_materia'] == [_('Este campo é obrigatório.')]
    assert errors['data'] == [_('Este campo é obrigatório.')]
    assert errors['hora_inicio'] == [_('Este campo é obrigatório.')]
    assert errors['hora_fim'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 9
