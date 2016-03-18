import pytest
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from comissoes.models import Comissao, TipoComissao

from .forms import MateriaAnexadaForm
from .models import (Anexada, Autor, Autoria, DespachoInicial,
                     MateriaLegislativa, RegimeTramitacao, TipoAutor,
                     TipoMateriaLegislativa)


@pytest.mark.django_db(transaction=False)
def make_materia_principal():
    regime_tramitacao = mommy.make(RegimeTramitacao, descricao='Teste_Regime')

    # Cria a matéria principal
    tipo = mommy.make(TipoMateriaLegislativa,
                      sigla='T1',
                      descricao='Teste_1')
    mommy.make(MateriaLegislativa,
               tipo=tipo,
               numero='165',
               ano='2002',
               data_apresentacao='2003-01-01',
               regime_tramitacao=regime_tramitacao)

    # Testa se a matéria principal foi criada
    return MateriaLegislativa.objects.get(numero=165, ano=2002)


@pytest.mark.django_db(transaction=False)
def test_materia_anexada_submit(client):
    materia_principal = make_materia_principal()

    # Cria a matéria que será anexada
    tipo_anexada = mommy.make(TipoMateriaLegislativa,
                              sigla='T2',
                              descricao='Teste_2')
    regime_tramitacao = mommy.make(RegimeTramitacao, descricao='Teste_Regime')
    mommy.make(MateriaLegislativa,
               tipo=tipo_anexada,
               numero='32',
               ano='2004',
               data_apresentacao='2005-11-10',
               regime_tramitacao=regime_tramitacao)

    # Testa se a matéria que será anexada foi criada
    materia_anexada = MateriaLegislativa.objects.get(numero=32, ano=2004)

    # Testa POST
    response = client.post(reverse('materia_anexada',
                                   kwargs={'pk': materia_principal.pk}),
                           {'tipo': materia_anexada.tipo.pk,
                            'numero': materia_anexada.numero,
                            'ano': materia_anexada.ano,
                            'data_anexacao': '2016-03-18',
                            'salvar': 'salvar'},
                           follow=True)
    assert response.status_code == 200

    # Verifica se a matéria foi anexada corretamente
    anexada = Anexada.objects.first()
    assert anexada.materia_principal == materia_principal
    assert anexada.materia_anexada == materia_anexada


@pytest.mark.django_db(transaction=False)
def test_autoria_submit(client):
    materia_principal = make_materia_principal()

    # Cria um tipo de Autor
    tipo_autor = mommy.make(TipoAutor, descricao='Teste Tipo_Autor')

    # Cria um Autor
    autor = mommy.make(Autor, tipo=tipo_autor, nome='Autor Teste')

    # Testa POST
    response = client.post(reverse('autoria',
                                   kwargs={'pk': materia_principal.pk}),
                           {'autor': autor.pk,
                            'primeiro_autor': True,
                            'salvar': 'salvar'},
                           follow=True)
    assert response.status_code == 200

    # Verifica se o autor foi realmente criado
    autoria = Autoria.objects.first()
    assert autoria.autor == autor
    assert autoria.materia == materia_principal
    assert autoria.primeiro_autor is True


@pytest.mark.django_db(transaction=False)
def test_despacho_inicial_submit(client):
    materia_principal = make_materia_principal()

    # Cria uma comissão
    tipo_comissao = mommy.make(TipoComissao)
    comissao = mommy.make(Comissao,
                          tipo=tipo_comissao,
                          nome='Teste',
                          sigla='T',
                          data_criacao='2016-03-18')

    # Testa POST
    response = client.post(reverse('despacho_inicial',
                                   kwargs={'pk': materia_principal.pk}),
                           {'comissao': comissao.pk,
                            'salvar': 'salvar'},
                           follow=True)
    assert response.status_code == 200

    # Verifica se o despacho foi criado
    despacho = DespachoInicial.objects.first()
    assert despacho.comissao == comissao
    assert despacho.materia == materia_principal
