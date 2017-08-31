import pytest
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from sapl.parlamentares.models import Legislatura, Partido, SessaoLegislativa
from sapl.sessao import forms
from sapl.sessao.models import TipoSessaoPlenaria


def test_valida_campos_obrigatorios_sessao_plenaria_form():
    form = forms.SessaoPlenariaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['legislatura'] == [_('Este campo é obrigatório.')]
    assert errors['sessao_legislativa'] == [_('Este campo é obrigatório.')]
    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['numero'] == [_('Este campo é obrigatório.')]
    assert errors['data_inicio'] == [_('Este campo é obrigatório.')]
    assert errors['hora_inicio'] == [_('Este campo é obrigatório.')]

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


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_bancada_form():
    form = forms.BancadaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['legislatura'] == [_('Este campo é obrigatório.')]
    assert errors['nome'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 2


@pytest.mark.django_db(transaction=False)
def test_bancada_form_valido():
    legislatura = mommy.make(Legislatura)
    partido = mommy.make(Partido)

    form = forms.BancadaForm(data={'legislatura': str(legislatura.pk),
                                   'nome': 'Nome da Bancada',
                                   'partido': str(partido.pk),
                                   'data_criacao': '10/11/2017',
                                   'data_extincao': '10/12/2017',
                                   'descricao': 'teste'
                                   })

    assert form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_bancada_form_datas_invalidas():
    legislatura = mommy.make(Legislatura)
    partido = mommy.make(Partido)

    form = forms.BancadaForm(data={'legislatura': str(legislatura.pk),
                                   'nome': 'Nome da Bancada',
                                   'partido': str(partido.pk),
                                   'data_criacao': '2016-11-01',
                                   'data_extincao': '2016-10-01',
                                   'descricao': 'teste'
                                   })
    assert not form.is_valid()
    assert form.errors['__all__'] == [_('Data de extinção não pode ser menor '
                                        'que a de criação')]
