import pytest
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from sapl.parlamentares.models import Legislatura, SessaoLegislativa
from sapl.sessao.models import SessaoPlenaria, TipoSessaoPlenaria


@pytest.mark.django_db(transaction=False)
def test_incluir_sessao_plenaria_submit(admin_client):
    legislatura = mommy.make(Legislatura)
    sessao = mommy.make(SessaoLegislativa)
    tipo = mommy.make(TipoSessaoPlenaria, id=1)

    response = admin_client.post(reverse('sapl.sessao:sessaoplenaria_create'),
                                 {'legislatura': str(legislatura.pk),
                                  'numero': '1',
                                  'tipo': str(tipo.pk),
                                  'sessao_legislativa': str(sessao.pk),
                                  'data_inicio': '10/11/2017',
                                  'hora_inicio': '10:10'
                                  }, follow=True)

    assert response.status_code == 200

    sessao_plenaria = SessaoPlenaria.objects.first()
    assert sessao_plenaria.tipo == tipo


@pytest.mark.django_db(transaction=False)
def test_incluir_sessao_errors(admin_client):

    response = admin_client.post(reverse('sapl.sessao:sessaoplenaria_create'),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['legislatura'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['sessao_legislativa'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['tipo'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['numero'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['data_inicio'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['hora_inicio'] ==
            [_('Este campo é obrigatório.')])
