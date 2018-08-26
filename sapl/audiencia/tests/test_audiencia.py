import pytest
from sapl.translation import ugettext as _
from model_mommy import mommy

from sapl.audiencia import forms
from sapl.audiencia.models import TipoAudienciaPublica
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa

@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_audiencia_form():
    form = forms.AudienciaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['nome'] == [_('Este campo é obrigatório.')]
    assert errors['tema'] == [_('Este campo é obrigatório.')]
    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['data'] == [_('Este campo é obrigatório.')]
    assert errors['hora_inicio'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 5


@pytest.mark.django_db(transaction=False)
def test_audiencia_form_hora_invalida():
    tipo_materia = mommy.make(TipoMateriaLegislativa)

    tipo = mommy.make(TipoAudienciaPublica)

    form = forms.AudienciaForm(data={'nome': 'Nome da Audiencia',
                                     'tema': 'Tema da Audiencia',
                                     'tipo': tipo,
                                     'data': '2016-10-01',
                                     'hora_inicio': '10:00',
                                     'hora_fim': '9:00',
                                  	})
    assert not form.is_valid()

  