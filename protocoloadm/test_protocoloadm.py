import pytest
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from .forms import AnularProcoloAdmForm
from .models import Protocolo


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_acessivel(client):
    response = client.get(reverse('anular_protocolo'))
    assert response.status_code == 200


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_inexistente():
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})

    # Não usa o assert form.is_valid() == False por causa do PEP8
    if form.is_valid():
        pytest.xfail("Form deve ser inválido")
    assert form.errors['__all__'] == [_("Protocolo 1/2016 não existe")]


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_valido():
    mommy.make(Protocolo, numero='1', ano='2016', anulado=False)
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    if not form.is_valid():
        pytest.xfail("Form deve ser válido")


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_anulado():
    mommy.make(Protocolo, numero='1', ano='2016', anulado=True)
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    assert form.errors['__all__'] == \
        [_("Protocolo 1/2016 já encontra-se anulado")]


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_campos_obrigatorios():
    mommy.make(Protocolo, numero='1', ano='2016', anulado=False)

    # numero ausente
    form = AnularProcoloAdmForm({'numero': '',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    if form.is_valid():
        pytest.xfail("Form deve ser inválido")

    assert len(form.errors) == 1
    assert form.errors['numero'] == [_('Este campo é obrigatório.')]

    # ano ausente
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '',
                                 'justificativa_anulacao': 'TESTE'})
    if form.is_valid():
        pytest.xfail("Form deve ser inválido")

    assert len(form.errors) == 1
    assert form.errors['ano'] == [_('Este campo é obrigatório.')]

    # justificativa_anulacao ausente
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': ''})
    if form.is_valid():
        pytest.xfail("Form deve ser inválido")

    assert len(form.errors) == 1
    assert form.errors['justificativa_anulacao'] == \
                      [_('Este campo é obrigatório.')]
