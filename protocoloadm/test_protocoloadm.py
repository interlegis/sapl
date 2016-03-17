import pytest
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .views import AnularProtocoloAdmView
from .forms import AnularProcoloAdmForm
from .models import Protocolo
from model_mommy import mommy

from django.utils.translation import ugettext_lazy as _


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_acessivel(client):
    response = client.get(reverse('anular_protocolo'))
    assert response.status_code == 200


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_inexistente():
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    assert form.is_valid() == False
    assert form.errors['__all__'] == [_("Protocolo 1/2016 não existe")]


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_valido():
    protocolo = mommy.make(Protocolo, numero='1', ano='2016', anulado=False)
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    assert form.is_valid() == True

@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_campos_obrigatorios():
    protocolo = mommy.make(Protocolo, numero='1', ano='2016', anulado=False)

    # numero ausente
    form = AnularProcoloAdmForm({'numero': '',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    assert form.is_valid() == False
    assert len(form.errors) == 1
    assert form.errors['numero'] == [_('Este campo é obrigatório.')]

    # ano ausente
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '',
                                 'justificativa_anulacao': 'TESTE'})
    assert form.is_valid() == False
    assert len(form.errors) == 1
    assert form.errors['ano'] == [_('Este campo é obrigatório.')]

    # ano ausente
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': ''})
    assert form.is_valid() == False
    assert len(form.errors) == 1
    assert form.errors['justificativa_anulacao'] == [_('Este campo é obrigatório.')]


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_anulado():
    protocolo = mommy.make(Protocolo, numero='1', ano='2016', anulado=True)
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    assert form.errors['__all__'] == [_("Protocolo 1/2016 já encontra-se anulado")]
