import pytest
from django.utils.translation import ugettext as _
from model_mommy import mommy

from sapl.compilacao import forms
from sapl.compilacao.models import (PerfilEstruturalTextoArticulado,
                                    TipoNota)
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


def test_valida_campos_obrigatorios_nota_form():
    form = forms.NotaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['texto'] == [_('Este campo é obrigatório')]
    assert errors['publicidade'] == [_('Este campo é obrigatório.')]
    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['publicacao'] == [_('Este campo é obrigatório')]
    assert errors['efetividade'] == [_('Este campo é obrigatório')]
    assert errors['dispositivo'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 6


@pytest.mark.django_db(transaction=False)
def test_nota_form_invalido():
    tipo = mommy.make(TipoNota)

    form = forms.NotaForm(data={'titulo': 'titulo',
                                'texto': 'teste',
                                'url_externa': 'www.test.com',
                                'publicidade': 'publicidade',
                                'tipo': str(tipo.pk),
                                'publicacao': '10/05/2017',
                                'efetividade': '10/05/2017',
                                'dispositivo': 'dispositivo',
                                'pk': 'pk'
                                })

    assert not form.is_valid()
