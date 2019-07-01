import pytest
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Legislatura, Parlamentar, Partido, SessaoLegislativa
from sapl.sessao import forms
from sapl.sessao.models import (ExpedienteMateria, ExpedienteSessao,
                                IntegranteMesa, Orador, OrdemDia,
                                PresencaOrdemDia, RegistroVotacao,
                                SessaoPlenaria, SessaoPlenariaPresenca,
                                TipoResultadoVotacao, TipoSessaoPlenaria,
                                VotoParlamentar)

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
                                          'data_inicio': str(sessao.data_inicio),
                                          'hora_inicio': '10:10',
                                          'painel_aberto': False
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
                                          'data_inicio': sessao_plenaria.data_inicio,
                                          'hora_inicio': '10:10'
                                          })

    assert not form.is_valid()

    assert form.errors['__all__'] == ["Número de Sessão Plenária já existente "
                                      "para a Legislatura, Sessão Legislativa "
                                      "e Tipo informados. Favor escolher um "
                                      "número distinto."]


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


@pytest.mark.django_db(transaction=False)
def test_registro_votacao_tem_ordem_xor_expediente():

    def registro_votacao_com(ordem, expediente):
        return mommy.make(RegistroVotacao, ordem=ordem, expediente=expediente)

    ordem = mommy.make(OrdemDia)
    expediente = mommy.make(ExpedienteMateria)

    # a validação funciona com exatamente um dos campos preenchido
    registro_votacao_com(ordem, None).full_clean()
    registro_votacao_com(None, expediente).full_clean()

    # a validação NÃO funciona quando nenhum deles é preenchido
    with pytest.raises(ValidationError):
        registro_votacao_com(None, None).full_clean()

    # a validação NÃO funciona quando ambos são preenchidos
    with pytest.raises(ValidationError):
        registro_votacao_com(ordem, expediente).full_clean()

def create_sessao_plenaria():
    legislatura = mommy.make(Legislatura)
    sessao = mommy.make(SessaoLegislativa)
    tipo = mommy.make(TipoSessaoPlenaria)
    return mommy.make(SessaoPlenaria,
                               legislatura=legislatura,
                               sessao_legislativa=sessao,
                               tipo=tipo,
                               numero=1)

def create_materia_legislativa():
    tipo_materia = mommy.make(TipoMateriaLegislativa)
    return mommy.make(MateriaLegislativa, tipo=tipo_materia)

@pytest.mark.django_db(transaction=False)
def test_delete_sessao_plenaria_cascade_registro_votacao_ordemdia():
    materia = create_materia_legislativa()
    sessao_plenaria = create_sessao_plenaria()
    ordem = mommy.make(OrdemDia,
                       sessao_plenaria=sessao_plenaria,
                       materia=materia,
                       tipo_votacao='2')
    tipo_resultado_votacao = mommy.make(TipoResultadoVotacao,
                                        nome='ok',
                                        natureza="A")
    registro = mommy.make(RegistroVotacao,
                          tipo_resultado_votacao=tipo_resultado_votacao,
                          materia=materia,
                          ordem=ordem)
    presenca = mommy.make(PresencaOrdemDia,
                          sessao_plenaria=sessao_plenaria)
    parlamentar = mommy.make(Parlamentar)
    voto_parlamentar = mommy.make(VotoParlamentar,
                                  votacao=registro,
                                  parlamentar=parlamentar,
                                  ordem=ordem)
    sessao_plenaria.delete()
    presenca_filter = PresencaOrdemDia.objects.filter(
                        sessao_plenaria=sessao_plenaria).exists()
    ordem_filter = OrdemDia.objects.filter(
                        sessao_plenaria=sessao_plenaria).exists()
    registro_filter = RegistroVotacao.objects.filter(
                        tipo_resultado_votacao=tipo_resultado_votacao,
                        materia=materia,
                        ordem=ordem).exists()
    materia_filter = MateriaLegislativa.objects.filter(id=materia.id).exists()
    parlamentar_filter = Parlamentar.objects.exists()
    voto_parlamentar_filter = VotoParlamentar.objects.filter(
                                    ordem=ordem).exists()
    assert not registro_filter
    assert not ordem_filter
    assert not presenca_filter
    assert not voto_parlamentar_filter
    assert materia_filter # Não exclui materia
    assert parlamentar_filter # Não exclui Parlamentar

@pytest.mark.django_db(transaction=False)
def test_delete_sessao_plenaria_cascade_registro_votacao_expediente():
    materia = create_materia_legislativa()
    sessao_plenaria = create_sessao_plenaria()
    expediente = mommy.make(ExpedienteMateria,
                            sessao_plenaria=sessao_plenaria,
                            materia=materia,
                            tipo_votacao='2')
    tipo_resultado_votacao = mommy.make(TipoResultadoVotacao,
                                        nome='ok',
                                        natureza="A")
    registro = mommy.make(RegistroVotacao,
                          tipo_resultado_votacao=tipo_resultado_votacao,
                          materia=materia,
                          expediente=expediente)
    presenca = mommy.make(SessaoPlenariaPresenca,
                          sessao_plenaria=sessao_plenaria)
    parlamentar = mommy.make(Parlamentar)
    voto_parlamentar = mommy.make(VotoParlamentar,
                                  votacao=registro,
                                  parlamentar=parlamentar,
                                  expediente=expediente)
    sessao_plenaria.delete()
    expediente_filter = ExpedienteMateria.objects.filter(
                            sessao_plenaria=sessao_plenaria).exists()
    registro_filter = RegistroVotacao.objects.filter(
                        tipo_resultado_votacao=tipo_resultado_votacao,
                        materia=materia,
                        expediente=expediente).exists()
    presenca_filter = SessaoPlenariaPresenca.objects.filter(
                        sessao_plenaria=sessao_plenaria).exists()
    parlamentar_filter = Parlamentar.objects.exists()
    voto_parlamentar_filter = VotoParlamentar.objects.filter(
                                    expediente=expediente).exists()
    assert not registro_filter
    assert not expediente_filter
    assert not presenca_filter
    assert not voto_parlamentar_filter
    assert parlamentar_filter #  Não exclui Parlamentar


@pytest.mark.django_db(transaction=False)
def test_delete_sessao_plenaria_cascade_integrante_mesa():
    sessao_plenaria = create_sessao_plenaria()
    mesa = mommy.make(IntegranteMesa,sessao_plenaria=sessao_plenaria)
    sessao_plenaria.delete()
    mesa_filter = IntegranteMesa.objects.filter(sessao_plenaria=sessao_plenaria).exists()
    assert not mesa_filter

@pytest.mark.django_db(transaction=False)
def test_delete_sessao_plenaria_cascade_expedientesessao():
    sessao_plenaria = create_sessao_plenaria()
    expediente_sessao = mommy.make(ExpedienteSessao, sessao_plenaria=sessao_plenaria)
    sessao_plenaria.delete()
    expediente_sessao_filter = ExpedienteSessao.objects.filter(sessao_plenaria=sessao_plenaria).exists()
    assert not expediente_sessao_filter

@pytest.mark.django_db(transaction=False)
def test_delete_sessao_plenaria_cascade_orador():
    sessao_plenaria = create_sessao_plenaria()
    expediente_sessao = mommy.make(Orador, sessao_plenaria=sessao_plenaria)
    sessao_plenaria.delete()
    orador_filter = Orador.objects.filter(sessao_plenaria=sessao_plenaria).exists()
    assert not orador_filter
