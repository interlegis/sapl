import pytest
from django.core.urlresolvers import reverse
from model_mommy import mommy

from comissoes.models import Comissao, TipoComissao

from .crud import (NO_ENTRIES_MSG, build_crud, from_to, get_field_display,
                   make_pagination)

pytestmark = pytest.mark.django_db

# XXX These tests are based on comissoes app
#     but could be done with a stub one


@pytest.mark.parametrize("layout, result", [
    ([['Dados Complementares']], []),  # missing rows definition
    ([
        ['Dados Básicos',
         [('nome', 9), ('sigla', 3)],
         [('tipo', 3), ('data_criacao', 3), ('unidade_deliberativa', 3), ]
         ],
        ['Dados Complementares', [('finalidade', 12)]], ],
     ['nome', 'sigla', 'tipo', 'data_criacao', 'unidade_deliberativa']),
])
def test_listview_get_fieldnames(layout, result):
    crud = build_crud(Comissao, 'stub_help_path', layout)
    view = crud.CrudListView()
    assert view.field_names == result


__ = None  # for test readability


@pytest.mark.parametrize(
    "index, num_pages, result",
    [(i, k, from_to(1, k))
     for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
     for k in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
     ] + [
        (11, 11, [1, 2, 3, 4, 5, 6, 7, __, 10, (11)]),
        (10, 11, [1, 2, 3, 4, 5, 6, __, 9, (10), 11]),
        (9, 11, [1, 2, 3, 4, 5, __, 8, (9), 10, 11]),
        (8, 11, [1, 2, 3, 4, __, 7, (8), 9, 10, 11]),
        (7, 11, [1, 2, 3, __, 6, (7), 8, 9, 10, 11]),
        (6, 11, [1, 2, 3, 4, 5, (6), 7, __, 10, 11]),
        (5, 11, [1, 2, 3, 4, (5), 6, 7, __, 10, 11]),
        (4, 11, [1, 2, 3, (4), 5, 6, 7, __, 10, 11]),
        (3, 11, [1, 2, (3), 4, 5, 6, 7, __, 10, 11]),
        (2, 11, [1, (2), 3, 4, 5, 6, 7, __, 10, 11]),
        (1, 11, [(1), 2, 3, 4, 5, 6, 7, __, 10, 11]),

        (12, 12, [1, 2, 3, 4, 5, 6, 7, __, 11, (12)]),
        (11, 12, [1, 2, 3, 4, 5, 6, __, 10, (11), 12]),
        (10, 12, [1, 2, 3, 4, 5, __, 9, (10), 11, 12]),
        (9, 12, [1, 2, 3, 4, __, 8, (9), 10, 11, 12]),
        (8, 12, [1, 2, 3, __, 7, (8), 9, 10, 11, 12]),
        (7, 12, [1, 2, 3, __, 6, (7), 8, __, 11, 12]),
        (6, 12, [1, 2, 3, 4, 5, (6), 7, __, 11, 12]),
        (5, 12, [1, 2, 3, 4, (5), 6, 7, __, 11, 12]),
        (4, 12, [1, 2, 3, (4), 5, 6, 7, __, 11, 12]),
        (3, 12, [1, 2, (3), 4, 5, 6, 7, __, 11, 12]),
        (2, 12, [1, (2), 3, 4, 5, 6, 7, __, 11, 12]),
        (1, 12, [(1), 2, 3, 4, 5, 6, 7, __, 11, 12]),

        # some random entries
        (8, 22, [1, 2, 3, __, 7, (8), 9, __, 21, 22]),
        (1, 17, [(1), 2, 3, 4, 5, 6, 7, __, 16, 17]),
        (22, 25, [1, 2, 3, 4, __, 21, (22), 23, 24, 25]),
    ])
def test_make_pagination(index, num_pages, result):
    assert num_pages < 10 or len(result) == 10
    assert make_pagination(index, num_pages) == result


def test_get_field_display():
    stub = mommy.prepare(Comissao, unidade_deliberativa=True)
    assert get_field_display(stub, 'nome')[1] == stub.nome
    assert get_field_display(stub, 'tipo')[1] == str(stub.tipo)
    # must return choice display, not the value
    assert stub.unidade_deliberativa is True
    assert get_field_display(stub, 'unidade_deliberativa')[1] == 'Sim'

    # None is displayed as empty string
    assert stub.finalidade is None
    assert get_field_display(stub, 'finalidade')[1] == ''


def test_crud_detail_view_fieldsets(monkeypatch):

    crud = build_crud(
        Comissao, 'stub_help_path', [

            ['Dados Básicos',
             [('nome', 9), ('sigla', 3)],
             [('tipo', 3), ('data_criacao', 3), ('unidade_deliberativa', 3), ]
             ],

            ['Dados Complementares',
             [('finalidade', 12)]
             ],
        ])

    view = crud.CrudDetailView()
    stub = mommy.make(Comissao,
                      nome='nome!!!',
                      tipo__nome='tipo!!!',
                      sigla='sigla!!!',
                      data_criacao='2011-01-01',
                      unidade_deliberativa=True)

    # to test None displayed as empty string
    assert stub.finalidade is None

    def get_object():
        return stub
    monkeypatch.setattr(view, 'get_object', get_object)

    assert view.fieldsets == [
        {'legend': 'Dados Básicos',
         'rows': [[{'id': 'nome',
                    'span': 9,
                    'text': 'nome!!!',
                    'verbose_name': 'Nome'},
                   {'id': 'sigla',
                    'span': 3,
                    'text': 'sigla!!!',
                    'verbose_name': 'Sigla'}],

                  [{'id': 'tipo',
                    'span': 3,
                    'text': 'tipo!!!',
                    'verbose_name': 'Tipo'},
                   {'id': 'data_criacao',
                    'span': 3,
                    'text': '2011-01-01',
                    'verbose_name': 'Data de Criação'},
                   {'id': 'unidade_deliberativa',
                    'span': 3,
                    'text': 'Sim',
                    'verbose_name': 'Unidade Deliberativa'}]]},
        {'legend': 'Dados Complementares',
         'rows': [[{'id': 'finalidade',
                    'span': 12,
                    'text': '',
                    'verbose_name': 'Finalidade'}]]}]


def test_reverse():
    assert '/comissoes/' == reverse('comissao:list')
    assert '/comissoes/create' == reverse('comissao:create')
    assert '/comissoes/2' == reverse('comissao:detail', args=(2,))
    assert '/comissoes/2/edit' == reverse('comissao:update', args=(2,))
    assert '/comissoes/2/delete' == reverse('comissao:delete', args=(2,))


def assert_h1(res, title):
    assert res.html.find('main').find('h1').text == title


NO_ENTRIES_MSG = str(NO_ENTRIES_MSG)  # "unlazy"


def assert_on_list_page(res):
    assert_h1(res, 'Comissões')
    assert 'Adicionar Comissão' in res
    assert res.html.find('table') or NO_ENTRIES_MSG in res
    # XXX ... characterize better


def assert_on_create_page(res):
    assert_h1(res, 'Adicionar Comissão')
    form = res.form
    assert not any(
        form[k].value for k in form.fields if k != 'csrfmiddlewaretoken')


def assert_on_detail_page(res, stub_name):
    assert_h1(res, stub_name)
    assert not res.forms
    assert 'Editar' in res
    assert 'Excluir' in res


@pytest.mark.urls('sapl.teststubs.urls_for_list_test')
@pytest.mark.parametrize("num_entries, page_size, ranges, page_list", [
    (0, 6, [], []),
    (5, 5, [(0, 5)], []),
    (10, 5, [(0, 5), (5, 10)], ['«', '1', '2', '»']),
    (9, 4, [(0, 4), (4, 8), (8, 9)], ['«', '1', '2', '3', '»']),
])
def test_flux_list_paginate_detail(
        app, monkeypatch, num_entries, page_size, ranges, page_list):

    entries_labels = []
    for i in range(num_entries):
        # letter = next(letters)
        nome, sigla, tipo = 'nome %s' % i, 'sigla %s' % i, 'tipo %s' % i
        entries_labels.append([nome, sigla, tipo])
        mommy.make(Comissao, nome=nome, sigla=sigla, tipo__nome=tipo)

    from .teststubs.urls_for_list_test import crud
    crud.CrudListView.paginate_by = page_size

    res = app.get('/comissoes/')

    if num_entries == 0:
        assert_on_list_page(res)
        assert NO_ENTRIES_MSG in res
        # no table
        assert not res.html.find('table')
        # no pagination
        assert not res.html.find('ul', {'class': 'pagination'})
    else:
        def assert_at_page(res, i):
            assert_on_list_page(res)
            table = res.html.find('table')
            assert table
            header, *trs = table.findAll('tr')
            assert header.text.strip().split() == ['Nome', 'Sigla', 'Tipo']
            rows = [[td.text.strip() for td in tr.findAll('td')]
                    for tr in trs]

            start, end = ranges[i - 1]
            assert entries_labels[start:end] == rows

            paginator = res.html.find('ul', {'class': 'pagination'})
            if page_list:
                assert paginator
                assert paginator.text.strip().split() == page_list

        assert_at_page(res, 1)
        res_detail = res.click('nome 1')
        assert_on_detail_page(res_detail, 'nome 1')

        if len(ranges) > 1:
            res = res.click('2', href='page=2')
            assert_at_page(res, 2)

            fist_entry_on_2nd_page = 'nome %s' % page_size
            res_detail = res.click(fist_entry_on_2nd_page)
            assert_on_detail_page(res_detail, fist_entry_on_2nd_page)

            res = res.click('1', href='page=1')
            assert_at_page(res, 1)

        res_detail = res.click('nome 1')
        assert_on_detail_page(res_detail, 'nome 1')


@pytest.mark.parametrize("cancel, make_invalid_submit", [
    (a, b) for a in (True, False) for b in (True, False)])
def test_flux_list_create_detail(app, cancel, make_invalid_submit):

    # to have a couple an option for tipo field
    stub_tipo = mommy.make(TipoComissao)

    res = app.get('/comissoes/')

    # on list page
    assert_on_list_page(res)

    res = res.click('Adicionar Comissão')
    previous_objects = set(Comissao.objects.all())

    # on create page
    assert_on_create_page(res)

    # test bifurcation !
    if cancel:
        res = res.click('Cancelar')
        # back to list page
        assert_on_list_page(res)
        # db has not changed
        assert previous_objects == set(Comissao.objects.all())
    else:
        # and a test detour !
        if make_invalid_submit:
            # some fields are required => validation error
            res = res.form.submit()
            'Formulário inválido. O registro não foi criado.' in res
            assert_on_create_page(res)
            # db has not changed
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
        assert_on_detail_page(res, stub_name)
        assert 'Registro criado com sucesso!' in res
        [new_obj] = list(set(Comissao.objects.all()) - previous_objects)
        assert new_obj.nome == stub_name


def get_detail_page(app):
    stub = mommy.make(Comissao, nome='Comissão Stub')
    res = app.get('/comissoes/%s' % stub.id)
    # on detail page
    assert_on_detail_page(res, stub.nome)
    return stub, res


@pytest.mark.parametrize("cancel", [True, False])
def test_flux_detail_update_detail(app, cancel):
    stub, res = get_detail_page(app)
    res = res.click('Editar')

    # on update page
    assert_h1(res, stub.nome)

    # test bifurcation !
    if cancel:
        res = res.click('Cancelar')

        # back to detail page
        assert_on_detail_page(res, stub.nome)
        assert Comissao.objects.get(pk=stub.pk).nome == stub.nome
    else:
        form = res.form
        new_name = '### New Name ###'
        form['nome'] = new_name
        res = form.submit()

        # on redirect to detail page
        assert res.url.endswith('/comissoes/%s' % stub.id)
        res = res.follow()

        # back to detail page
        assert_on_detail_page(res, new_name)
        assert 'Registro alterado com sucesso!' in res
        assert Comissao.objects.get(pk=stub.pk).nome == new_name


@pytest.mark.parametrize("cancel", [True, False])
def test_flux_detail_delete_list(app, cancel):
    stub, res = get_detail_page(app)
    res = res.click('Excluir')

    # on delete page
    assert 'Tem certeza que deseja apagar' in res
    assert stub.nome in res

    # test bifurcation !
    if cancel:
        res = res.click('Cancelar')

        # back to detail page
        assert_on_detail_page(res, stub.nome)
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
