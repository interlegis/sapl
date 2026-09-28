import pytest
from django.utils.translation import ugettext_lazy as _

from sapl.base.forms import CasaLegislativaForm


def test_valida_campos_obrigatorios_casa_legislativa_form():
    form = CasaLegislativaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['nome'] == [_('Este campo é obrigatório.')]
    assert errors['sigla'] == [_('Este campo é obrigatório.')]
    assert errors['endereco'] == [_('Este campo é obrigatório.')]
    assert errors['cep'] == [_('Este campo é obrigatório.')]
    assert errors['municipio'] == [_('Este campo é obrigatório.')]
    assert errors['uf'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 6


@pytest.mark.django_db(transaction=False)
def test_casa_legislativa_form_invalido():
    form = CasaLegislativaForm(data={'codigo': 'codigo',
                                     'nome': 'nome',
                                     'sigla': 'sg',
                                     'endereco': 'endereco',
                                     'cep': '7000000',
                                     'municipio': 'municipio',
                                     'uf': 'uf',
                                     'telefone': '33333333',
                                     'fax': '33333333',
                                     'logotipo': 'image',
                                     'endereco_web': 'web',
                                     'email': 'email',
                                     'informacao_geral': 'informacao_geral'
                                     })

    assert not form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_casa_legislativa_form_informacao_geral_sem_limite():
    # O campo é editado por editor de texto rico, então o valor submetido é
    # HTML: as tags não podem consumir um limite de caracteres.
    html = ''.join('<p>%s</p>' % linha for linha in
                   ['Câmara Municipal', 'Rua Osvaldo Cruz, 555 - Centro',
                    'Expediente das 8h às 12h e das 13h30 às 17h30'])
    assert len(html) > 100

    form = CasaLegislativaForm(data={'codigo': 'codigo',
                                     'nome': 'nome',
                                     'sigla': 'sg',
                                     'endereco': 'endereco',
                                     'cep': '70000-000',
                                     'municipio': 'municipio',
                                     'uf': 'DF',
                                     'telefone': '33333333',
                                     'fax': '33333333',
                                     'endereco_web': '',
                                     'email': '',
                                     'informacao_geral': html
                                     })

    assert form.is_valid(), form.errors
    assert form.cleaned_data['informacao_geral'] == html
