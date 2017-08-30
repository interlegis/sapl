import pytest
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from sapl.parlamentares.models import Legislatura, SessaoLegislativa
from sapl.sessao import forms
from sapl.sessao.models import SessaoPlenaria, TipoSessaoPlenaria


def test_valida_campos_obrigatorios_sessao_plenaria_form():
    form = forms.SessaoPlenariaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['legislatura'] == ['Este campo é obrigatório.']
    assert errors['sessao_legislativa'] == ['Este campo é obrigatório.']
    assert errors['tipo'] == ['Este campo é obrigatório.']
    assert errors['numero'] == ['Este campo é obrigatório.']
    assert errors['data_inicio'] == ['Este campo é obrigatório.']
    assert errors['hora_inicio'] == ['Este campo é obrigatório.']

    assert len(errors) == 6


@pytest.mark.django_db(transaction=False)
def test_sessao_plenaria_form_valido():
    legislatura = mommy.make(Legislatura)
    sessao = mommy.make(SessaoLegislativa)
    tipo = mommy.make(TipoSessaoPlenaria)

    form = forms.SessaoPlenariaForm(data={'legislatura': str(legislatura.pk),
                                          'numero': '1',
                                          'tipo': str(tipo.pk),
                                          'sessao_legislativa': str(sessao.pk),
                                          'data_inicio': '10/11/2017',
                                          'hora_inicio': '10:10'
                                          })

    assert form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_numero_duplicado_sessao_plenaria_form():
    legislatura = mommy.make(Legislatura)
    sessao = mommy.make(SessaoLegislativa)
    tipo = mommy.make(TipoSessaoPlenaria)
    sessao_plenaria = mommy.make(SessaoPlenaria,
                                 legislatura=legislatura,
                                 sessao_legislativa=sessao,
                                 tipo=tipo,
                                 numero=1)

    form = forms.SessaoPlenariaForm(data={'legislatura': str(legislatura.pk),
                                          'numero': '1',
                                          'tipo': str(tipo.pk),
                                          'sessao_legislativa': str(sessao.pk),
                                          'data_inicio': '10/11/2017',
                                          'hora_inicio': '10:10'
                                          })

    assert not form.is_valid()

    assert form.errors['__all__'] == ["Número de Sessão Plenária já existente "
                                      "para a Legislatura, Sessão Legislativa "
                                      "e Tipo informados. Favor escolher um "
                                      "número distinto."]
