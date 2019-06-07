import pytest
from django.utils.translation import ugettext as _
from model_mommy import mommy

from sapl.comissoes.models import Comissao, TipoComissao
from sapl.materia import forms
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_ficha_pesquisa_form():
    form = forms.FichaPesquisaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['tipo_materia'] == [_('Este campo é obrigatório.')]
    assert errors['data_inicial'] == [_('Este campo é obrigatório.')]
    assert errors['data_final'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 3


@pytest.mark.django_db(transaction=False)
def test_ficha_pesquisa_form_datas_invalidas():
    tipo = mommy.make(TipoMateriaLegislativa)

    form = forms.FichaPesquisaForm(data={'tipo_materia': str(tipo.pk),
                                         'data_inicial': '10/11/2017',
                                         'data_final': '09/11/2017'
                                         })
    assert not form.is_valid()
    assert form.errors['__all__'] == [_('A Data Final não pode ser menor que '
                                        'a Data Inicial')]


@pytest.mark.django_db(transaction=False)
def test_ficha_pesquisa_form_invalido():
    tipo = mommy.make(TipoMateriaLegislativa)

    form = forms.FichaPesquisaForm(data={'tipo_materia': str(tipo.pk),
                                         'data_inicial': '10/11/2017',
                                         'data_final': '09/11/2017'
                                         })

    assert not form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_ficha_seleciona_form():
    form = forms.FichaSelecionaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['materia'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 1


@pytest.mark.django_db(transaction=False)
def test_ficha_seleciona_form_valido():
    materia = mommy.make(MateriaLegislativa)

    form = forms.FichaSelecionaForm(data={'materia': str(materia.pk)})

    assert form.is_valid()


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_materialegislativa_form():
    form = forms.MateriaLegislativaForm(data={})

    assert not form.is_valid()

    errors = form.errors
    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['ano'] == [_('Este campo é obrigatório.')]
    assert errors['data_apresentacao'] == [_('Este campo é obrigatório.')]
    assert errors['numero'] == [_('Este campo é obrigatório.')]
    assert errors['ementa'] == [_('Este campo é obrigatório.')]
    assert errors['regime_tramitacao'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 6


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_unidade_tramitacao_form():
    form = forms.UnidadeTramitacaoForm(data={})

    assert not form.is_valid()
    errors = form.errors

    assert errors['__all__'] == [_('Somente um campo deve ser preenchido!')]

@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_orgao_form():
    form = forms.OrgaoForm(data={})

    assert not form.is_valid()
    errors = form.errors

    assert errors['nome'] == [_('Este campo é obrigatório.')]
    assert errors['sigla'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 2


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_materia_assunto_form():
    form = forms.MateriaAssuntoForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['assunto'] == [_('Este campo é obrigatório.')]
    assert errors['materia'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 2

@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_autoria_form():
    form = forms.AutoriaForm(data={},instance=None)

    assert not form.is_valid()

    errors = form.errors

    assert len(errors) == 3

    assert errors['tipo_autor'] == [_('Este campo é obrigatório.')]
    assert errors['autor'] == [_('Este campo é obrigatório.')]
    assert errors['primeiro_autor'] == [_('Este campo é obrigatório.')]


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_autoria_multicreate_form():
    form = forms.AutoriaMultiCreateForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert len(errors) == 4

    assert errors['__all__'] == [_('Ao menos um autor deve ser selecionado para inclusão')]
    assert errors['tipo_autor'] == [_('Este campo é obrigatório.')]
    assert errors['autor'] == [_('Este campo é obrigatório.')]
    assert errors['primeiro_autor'] == [_('Este campo é obrigatório.')]


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_tipo_proposicao_form():
    form = forms.TipoProposicaoForm(data={})

    assert not form.is_valid()

    errors = form.errors
    assert errors['tipo_conteudo_related'] == [_('Este campo é obrigatório.')]
    assert errors['descricao'] == [_('Este campo é obrigatório.')]
    assert errors['content_type'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 3

@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_devolver_proposicao_form():
    form = forms.DevolverProposicaoForm(data={})

    assert not form.is_valid()

    errors = form.errors
    assert errors['__all__'] == [_('Adicione uma Justificativa para devolução.')]

    assert len(errors) == 1

@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_relatoria_form():
    tipo_comissao = mommy.make(TipoComissao)
    comissao = mommy.make(Comissao,
                          tipo=tipo_comissao,
                          nome='Comissao Teste',
                          sigla='T',
                          data_criacao='2016-03-21')
    form = forms.RelatoriaForm(initial={'comissao':comissao}, data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['parlamentar'] == [_('Este campo é obrigatório.')]
    assert errors['data_designacao_relator'] == [_('Este campo é obrigatório.')]
    assert errors['composicao'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 3


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_tramitacao_form():
    form = forms.TramitacaoForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['unidade_tramitacao_local'] == [_('Este campo é obrigatório.')]
    assert errors['texto'] == [_('Este campo é obrigatório.')]
    assert errors['status'] == [_('Este campo é obrigatório.')]
    assert errors['data_tramitacao'] == [_('Este campo é obrigatório.')]
    assert errors['unidade_tramitacao_destino'] == [_('Este campo é obrigatório.')]
    assert errors['urgente'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 6


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_tramitacao_update_form():
    form = forms.TramitacaoUpdateForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['unidade_tramitacao_local'] == [_('Este campo é obrigatório.')]
    assert errors['texto'] == [_('Este campo é obrigatório.')]
    assert errors['status'] == [_('Este campo é obrigatório.')]
    assert errors['data_tramitacao'] == [_('Este campo é obrigatório.')]
    assert errors['unidade_tramitacao_destino'] == [_('Este campo é obrigatório.')]
    assert errors['urgente'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 6


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_legislacao_citada_form():
    form = forms.LegislacaoCitadaForm(data={})

    assert not form.is_valid()

    errors = form.errors
    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['ano'] == [_('Este campo é obrigatório.')]
    assert errors['numero'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 3


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_numeracao_form():
    form = forms.NumeracaoForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['tipo_materia'] == [_('Este campo é obrigatório.')]
    assert errors['ano_materia'] == [_('Este campo é obrigatório.')]
    assert errors['numero_materia'] == [_('Este campo é obrigatório.')]
    assert errors['data_materia'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 4


@pytest.mark.django_db(transaction=False)
def test_valida_campos_obrigatorios_anexada_form():
    form = forms.AnexadaForm(data={})

    assert not form.is_valid()

    errors = form.errors

    assert errors['tipo'] == [_('Este campo é obrigatório.')]
    assert errors['ano'] == [_('Este campo é obrigatório.')]
    assert errors['numero'] == [_('Este campo é obrigatório.')]
    assert errors['data_anexacao'] == [_('Este campo é obrigatório.')]

    assert len(errors) == 4
