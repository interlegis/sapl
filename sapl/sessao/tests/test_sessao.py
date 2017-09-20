import pytest
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from sapl.materia.models import TipoMateriaLegislativa, MateriaLegislativa
from sapl.parlamentares.models import Legislatura, Partido, SessaoLegislativa
from sapl.sessao import forms
from sapl.sessao.models import (ExpedienteMateria, SessaoPlenaria,
                                TipoSessaoPlenaria)


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
    mommy.make(SessaoPlenaria,
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


@pytest.mark.django_db(transaction=False)
def test_expediente_materia_form_valido():
    tipo_materia = mommy.make(TipoMateriaLegislativa)
    materia = mommy.make(MateriaLegislativa, tipo=tipo_materia)

    sessao = mommy.make(SessaoPlenaria)

    instance = mommy.make(ExpedienteMateria, sessao_plenaria=sessao,
                          materia=materia)

    form = forms.ExpedienteMateriaForm(data={'data_ordem': '28/12/2009',
                                             'numero_ordem': 1,
                                             'tipo_materia': tipo_materia.pk,
                                             'numero_materia': materia.numero,
                                             'ano_materia': materia.ano,
                                             'tipo_votacao': 1,
                                             'sessao_plenaria': sessao.pk
                                             },
                                       instance=instance)
    assert form.is_valid()
