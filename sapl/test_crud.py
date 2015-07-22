import pytest
from django.core.urlresolvers import reverse
from model_mommy import mommy

from comissoes.models import Comissao, TipoComissao


# XXX These tests are based on comissoes app
#     but could be done with a stub one


def test_reverse():
    assert '/comissoes/' == reverse('comissao:list')
    assert '/comissoes/create' == reverse('comissao:create')
    assert '/comissoes/2' == reverse('comissao:detail', args=(2,))
    assert '/comissoes/2/edit' == reverse('comissao:update', args=(2,))
    assert '/comissoes/2/delete' == reverse('comissao:delete', args=(2,))


def assert_h1(res, title):
    assert res.html.find('h1').text == title


def assert_on_create_page(res):
    assert_h1(res, 'Adicionar Comissão')
    form = res.form
    assert not any(
        form[k].value for k in form.fields if k != 'csrfmiddlewaretoken')


def assert_on_detail_page(res, stub_name):
    assert_h1(res, stub_name)
    assert not res.forms
    assert 'Editar Comissão' in res
    assert 'Excluir Comissão' in res


@pytest.mark.parametrize("make_invalid_submit", [True, False])
def test_flux_list_create_detail(app, make_invalid_submit):

    # to have a couple an option for tipo field
    stub_tipo = mommy.make(TipoComissao)

    res = app.get('/comissoes/')

    # on list page
    assert_h1(res, 'Comissões')
    res = res.click('Adicionar Comissão')
    previous_objects = set(Comissao.objects.all())

    # on create page
    assert_on_create_page(res)

    # test bifurcation !
    if make_invalid_submit:
        # some fields are required => validation error
        res = res.form.submit()
        'Formulário inválido. O registro não foi criado.' in res
        assert_on_create_page(res)
        assert previous_objects == set(Comissao.objects.all())

    # now fill out some fields
    form = res.form
    stub_name = '### Nome Especial ###'
    form['nome'] = stub_name
    form['sigla'] = 'SIGLA'
    form['tipo'] = stub_tipo.id
    form['data_criacao'] = '1/1/2001'
    res = form.submit()

    # on redirect to detail page
    created = Comissao.objects.get(nome=stub_name)
    assert res.url.endswith('/comissoes/%s' % created.id)
    res = res.follow()

    # on detail page
    assert 'Registro criado com sucesso!' in res
    assert_on_detail_page(res, stub_name)
    [new_obj] = list(set(Comissao.objects.all()) - previous_objects)
    assert new_obj.nome == stub_name


def get_detail_page(app):
    stub = mommy.make(Comissao, nome='Comissão Stub')
    res = app.get('/comissoes/%s' % stub.id)
    # on detail page
    assert_on_detail_page(res, stub.nome)
    return stub, res


def test_flux_detail_update_detail(app):
    stub, res = get_detail_page(app)
    res = res.click('Editar Comissão')

    # on update page
    assert_h1(res, stub.nome)
    form = res.form
    new_name = '### New Name ###'
    form['nome'] = new_name
    res = form.submit()

    # on redirect to detail page
    assert res.url.endswith('/comissoes/%s' % stub.id)
    res = res.follow()

    # back to detail page
    assert 'Registro alterado com sucesso!' in res
    assert_h1(res, new_name)
    assert Comissao.objects.get(pk=stub.pk).nome == new_name


@pytest.mark.parametrize("cancel", [True, False])
def test_flux_detail_delete_list(app, cancel):
    stub, res = get_detail_page(app)
    res = res.click('Excluir Comissão')

    # on delete page
    assert 'Tem certeza que deseja apagar' in res
    assert stub.nome in res

    # test bifurcation !
    if cancel:
        res = res.click('Cancelar')

        # back to detail page
        assert_h1(res, stub.nome)
        assert Comissao.objects.filter(pk=stub.pk)
    else:
        res = res.form.submit()

        # on redirect to list page
        assert res.url.endswith('/comissoes/')
        res = res.follow()

        # on list page
        assert 'Registro excluído com sucesso!' in res
        assert_h1(res, 'Comissões')
        assert not Comissao.objects.filter(pk=stub.pk)
