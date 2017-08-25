from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy
import pytest

from sapl.compilacao import forms
from sapl.compilacao.models import PerfilEstruturalTextoArticulado
from sapl.compilacao.views import choice_models_in_extenal_views


def test_valida_campos_obrigatorios_tipo_texto_articulado_form():
    form = forms.TipoTaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['sigla'] == [_('Este campo é obrigatório.')]
    assert errors['descricao'] == [_('Este campo é obrigatório.')]
    assert errors['participacao_social'] == [_('Este campo é obrigatório.')]
    assert errors['publicacao_func'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 4


_content_types = choice_models_in_extenal_views()


@pytest.mark.parametrize('content_type', _content_types)
@pytest.mark.django_db(transaction=False)
def test_tipo_texto_articulado_form_valid(content_type):
    perfil = mommy.make(PerfilEstruturalTextoArticulado)

    form = forms.TipoTaForm(data={'sigla': 'si',
                                  'descricao': 'teste',
                                  'content_type': content_type[0],
                                  'participacao_social': True,
                                  'publicacao_func': True,
                                  'perfis': [perfil.pk, ]
                                  })

    assert form.is_valid(), form.errors
