import pytest
import datetime
from model_mommy import mommy
from django.utils.translation import ugettext as _

from sapl.audiencia import forms
from sapl.audiencia.models import AnexoAudienciaPublica
from sapl.audiencia.models import TipoAudienciaPublica, AudienciaPublica
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa


@pytest.mark.django_db(transaction=False)
def test_tipo_audiencia_publica_model():
    mommy.make(TipoAudienciaPublica,
               nome='Teste_Nome_Tipo_Audiencia_Publica',
               tipo='A')

    tipo_audiencia_publica = TipoAudienciaPublica.objects.first()
    assert tipo_audiencia_publica.nome == 'Teste_Nome_Tipo_Audiencia_Publica'
    assert tipo_audiencia_publica.tipo == 'A'


@pytest.mark.django_db(transaction=False)
def test_audiencia_publica_model():
    mommy.make(AudienciaPublica,
               numero=1,
               nome='Teste_Nome_Audiencia_Publica',
               tema='Teste_Tema_Audiencia_Publica',
               data='2016-03-21',
               hora_inicio='16:03')

    audiencia_publica = AudienciaPublica.objects.first()

    data = '2016-03-21'
    teste_data = datetime.datetime.strptime(data, "%Y-%m-%d").date()

    assert audiencia_publica.numero == 1
    assert audiencia_publica.nome == 'Teste_Nome_Audiencia_Publica'
    assert audiencia_publica.tema == 'Teste_Tema_Audiencia_Publica'
    assert audiencia_publica.data == teste_data
    assert audiencia_publica.hora_inicio == '16:03'


@pytest.mark.django_db(transaction=False)
def test_anexo_audiencia_publica_model():
    audiencia = mommy.make(AudienciaPublica,
                           numero=2,
                           nome='Nome_Audiencia_Publica',
                           tema='Tema_Audiencia_Publica',
                           data='2017-04-22',
                           hora_inicio='17:04')

    mommy.make(AnexoAudienciaPublica,
               audiencia=audiencia)

    anexo_audiencia_publica = AnexoAudienciaPublica.objects.first()
    assert anexo_audiencia_publica.audiencia == audiencia


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_audiencia_form():
    form = forms.AudienciaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['nome'] == [_('Este campo é obrigatório.')]
    assert errors['tema'] == [_('Este campo é obrigatório.')]
    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['data'] == [_('Este campo é obrigatório.')]
    assert errors['hora_inicio'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 5


@pytest.mark.django_db(transaction=False)
def test_audiencia_form_hora_invalida():
    tipo_materia = mommy.make(TipoMateriaLegislativa)

    tipo = mommy.make(TipoAudienciaPublica)

    form = forms.AudienciaForm(data={'nome': 'Nome da Audiencia',
                                     'tema': 'Tema da Audiencia',
                                     'tipo': tipo,
                                     'data': '2016-10-01',
                                     'hora_inicio': '10:00',
                                     'hora_fim': '9:00',
                                     })
    assert not form.is_valid()
