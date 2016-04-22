import pytest
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from protocoloadm.forms import AnularProcoloAdmForm
from protocoloadm.models import Protocolo


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_acessivel(client):
    response = client.get(reverse('protocoloadm:anular_protocolo'))
    assert response.status_code == 200


@pytest.mark.django_db(transaction=False)
def test_anular_protocolo_submit(client):
    mommy.make(Protocolo, numero='76', ano='2016', anulado=False)

    # TODO: setar usuario e IP
    response = client.post(reverse('protocoloadm:anular_protocolo'),
                           {'numero': '76',
                            'ano': '2016',
                            'justificativa_anulacao': 'TESTE',
                            'salvar': 'Anular'},
                           follow=True)

    assert response.status_code == 200

    protocolo = Protocolo.objects.first()
    assert protocolo.numero == 76
    assert protocolo.ano == 2016

    if not protocolo.anulado:
        pytest.fail(_("Protocolo deveria estar anulado"))
    assert protocolo.justificativa_anulacao == 'TESTE'


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_inexistente():
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})

    # Não usa o assert form.is_valid() == False por causa do PEP8
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))
    assert form.errors['__all__'] == [_("Protocolo 1/2016 não existe")]


@pytest.mark.django_db(transaction=False)
def test_form_anular_protocolo_valido():
    mommy.make(Protocolo, numero='1', ano='2016', anulado=False)
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    if not form.is_valid():
        pytest.fail(_("Form deve ser válido"))


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

    # TODO: generalizar para diminuir o tamanho deste método

    # numero ausente
    form = AnularProcoloAdmForm({'numero': '',
                                 'ano': '2016',
                                 'justificativa_anulacao': 'TESTE'})
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))

    assert len(form.errors) == 1
    assert form.errors['numero'] == [_('Este campo é obrigatório.')]

    # ano ausente
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '',
                                 'justificativa_anulacao': 'TESTE'})
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))

    assert len(form.errors) == 1
    assert form.errors['ano'] == [_('Este campo é obrigatório.')]

    # justificativa_anulacao ausente
    form = AnularProcoloAdmForm({'numero': '1',
                                 'ano': '2016',
                                 'justificativa_anulacao': ''})
    if form.is_valid():
        pytest.fail(_("Form deve ser inválido"))

    assert len(form.errors) == 1
    assert form.errors['justificativa_anulacao'] == \
                      [_('Este campo é obrigatório.')]
