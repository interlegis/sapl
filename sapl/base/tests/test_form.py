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
