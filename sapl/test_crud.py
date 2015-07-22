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


def test_flux_list_create_detail(app):

    # to have a couple an option for tipo field
    stub_tipo = mommy.make(TipoComissao)

    res = app.get('/comissoes/')
    print(res.url)

    # on list page
    assert_h1(res, 'Comissões')
    res = res.click('Adicionar Comissão')
    print(res.url)

    # on create page
    assert_h1(res, 'Adicionar Comissão')
    form = res.form
    assert not any(
        form[k].value for k in form.fields if k != 'csrfmiddlewaretoken')

    # some fields are required => validation error
    res = res.form.submit()
    print(res.url)
    'Formulário inválido. O registro não foi criado.' in res

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
    assert res.url.endswith('comissoes/%s' % created.id)
    res = res.follow()

    # on detail page
    assert 'Registro criado com sucesso!' in res
    assert_h1(res, stub_name)


def test_flux_detail_update_detail(app):

    stub_name = 'Comissão Stub'
    stub = mommy.make(Comissao, nome=stub_name)
    res = app.get('/comissoes/%s' % stub.id)
    assert_h1(res, stub_name)
    assert not res.forms
    res = res.click('Editar Comissão')
