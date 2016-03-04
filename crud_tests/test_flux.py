"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
import pytest
from django.core.urlresolvers import reverse
from model_mommy import mommy

from crud import (CrispyLayoutFormMixin, CrudListMixin, from_to,
                  get_field_display, make_pagination)

from .models import Continent, Country
from .views import CountryCrudListMixin

pytestmark = pytest.mark.django_db


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
    stub = mommy.prepare(Country, is_cold=True)
    assert get_field_display(stub, 'name')[1] == stub.name
    assert get_field_display(stub, 'continent')[1] == str(stub.continent)
    # must return choice display, not the value
    assert stub.is_cold is True
    assert get_field_display(stub, 'is_cold')[1] == 'Yes'

    # None is displayed as an empty string
    assert stub.population is None
    assert get_field_display(stub, 'population')[1] == ''


@pytest.mark.parametrize("_layout, result", [
    ([['Dados Complementares']], []),  # missing rows definition

    ([['Basic', [('name', 9), ('population', 3)]],
      ['More Details', [('description', 12)]],
      ],
     ['name', 'population']),
])
def test_layout_fieldnames(_layout, result):

    class StubMixin(CrispyLayoutFormMixin):

        def get_layout(self):
            return _layout

    view = StubMixin()
    assert view.list_field_names == result


def test_layout_detail_fieldsets(monkeypatch):

    stub = mommy.make(Country,
                      name='Brazil',
                      continent__name='South America',
                      is_cold=False)

    class StubMixin(CrispyLayoutFormMixin):

        def get_layout(self):
            return [['Basic Data',
                     [('name', 9), ('continent', 3)],
                     [('population', 6), ('is_cold', 6)]
                     ],
                    ['More Details', [('description', 12)]],
                    ]

        def get_object(self):
            return stub

    view = StubMixin()

    # to test None displayed as empty string
    assert stub.population is None

    assert view.layout_display == [
        {'legend': 'Basic Data',
         'rows': [[{'id': 'name',
                    'span': 9,
                    'text': stub.name,
                    'verbose_name': 'name'},
                   {'id': 'continent',
                    'span': 3,
                    'text': stub.continent.name,
                    'verbose_name': 'continent'}
                   ],

                  [{'id': 'population',
                    'span': 6,
                    'text': '',
                    'verbose_name': 'population'},
                   {'id': 'is_cold',
                    'span': 6,
                    'text': 'No',
                    'verbose_name': 'is cold'}]]},
        {'legend': 'More Details',
         'rows': [[{'id': 'description',
                    'span': 12,
                    'text': '',
                    'verbose_name': 'description'}]]}]


def test_reverse():
    assert '/countries/' == reverse('country:list')
    assert '/countries/create' == reverse('country:create')
    assert '/countries/2' == reverse('country:detail', args=(2,))
    assert '/countries/2/edit' == reverse('country:update', args=(2,))
    assert '/countries/2/delete' == reverse('country:delete', args=(2,))


def assert_h1(res, title):
    assert res.html.find('main').find('h1').text == title


NO_ENTRIES_MSG = str(CrudListMixin.no_entries_msg)  # "unlazy"


def assert_on_list_page(res):
    assert_h1(res, 'Countries')
    assert 'Adicionar Country' in res
    assert res.html.find('table') or NO_ENTRIES_MSG in res
    # XXX ... characterize better


def assert_on_create_page(res):
    assert_h1(res, 'Adicionar Country')
    form = res.form
    assert not any(
        form[k].value for k in form.fields if k != 'csrfmiddlewaretoken')


def assert_on_detail_page(res, stub_name):
    assert_h1(res, stub_name)
    assert not res.forms
    assert 'Editar' in res
    assert 'Excluir' in res


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
        name, continent = 'name %s' % i, 'continent %s' % i
        population, is_cold = i, i % 2 == 0
        entries_labels.append([
            name, continent, str(population), 'Yes' if is_cold else 'No'])
        mommy.make(Country,
                   name=name,
                   continent__name=continent,
                   population=population,
                   is_cold=is_cold)

    CountryCrudListMixin.paginate_by = page_size

    res = app.get('/countries/')

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
            header_trs = table.findAll('tr')
            header, trs = header_trs[0], header_trs[1:]
            assert [c.text for c in header.findChildren('th')] == [
                'name', 'continent', 'population', 'is cold']
            rows = [[td.text.strip() for td in tr.findAll('td')]
                    for tr in trs]

            start, end = ranges[i - 1]
            assert entries_labels[start:end] == rows

            paginator = res.html.find('ul', {'class': 'pagination'})
            if page_list:
                assert paginator
                assert paginator.text.strip().split() == page_list

        assert_at_page(res, 1)
        res_detail = res.click('name 1')
        assert_on_detail_page(res_detail, 'name 1')

        if len(ranges) > 1:
            res = res.click('2', href='page=2')
            assert_at_page(res, 2)

            fist_entry_on_2nd_page = 'name %s' % page_size
            res_detail = res.click(fist_entry_on_2nd_page)
            assert_on_detail_page(res_detail, fist_entry_on_2nd_page)

            res = res.click('1', href='page=1')
            assert_at_page(res, 1)

        res_detail = res.click('name 1')
        assert_on_detail_page(res_detail, 'name 1')


@pytest.mark.parametrize("cancel, make_invalid_submit", [
    (a, b) for a in (True, False) for b in (True, False)])
def test_flux_list_create_detail(app, cancel, make_invalid_submit):

    # to have a couple an option for continent field
    stub_continent = mommy.make(Continent)

    res = app.get('/countries/')

    # on list page
    assert_on_list_page(res)

    res = res.click('Adicionar Country')
    previous_objects = set(Country.objects.all())

    # on create page
    assert_on_create_page(res)

    # test bifurcation !
    if cancel:
        res = res.click('Cancelar')
        # back to list page
        assert_on_list_page(res)
        # db has not changed
        assert previous_objects == set(Country.objects.all())
    else:
        # and a test detour !
        if make_invalid_submit:
            # some fields are required => validation error
            res = res.form.submit()
            'Formulário inválido. O registro não foi criado.' in res
            assert_on_create_page(res)
            # db has not changed
            assert previous_objects == set(Country.objects.all())

        # now fill out some fields
        form = res.form
        stub_name = '### name ###'
        form['name'] = stub_name
        form['continent'] = stub_continent.id
        form['population'] = 23000
        form['is_cold'] = True
        res = form.submit()

        # on redirect to detail page
        created = Country.objects.get(name=stub_name)
        assert res.url.endswith('/countries/%s' % created.id)
        res = res.follow()

        # on detail page
        assert_on_detail_page(res, stub_name)
        assert 'Registro criado com sucesso!' in res
        [new_obj] = list(set(Country.objects.all()) - previous_objects)
        assert new_obj.name == stub_name


def get_detail_page(app):
    stub = mommy.make(Country, name='Country Stub')
    res = app.get('/countries/%s' % stub.id)
    # on detail page
    assert_on_detail_page(res, stub.name)
    return stub, res


@pytest.mark.parametrize("cancel", [True, False])
def test_flux_detail_update_detail(app, cancel):
    stub, res = get_detail_page(app)
    res = res.click('Editar')

    # on update page
    assert_h1(res, stub.name)

    # test bifurcation !
    if cancel:
        res = res.click('Cancelar')

        # back to detail page
        assert_on_detail_page(res, stub.name)
        assert Country.objects.get(pk=stub.pk).name == stub.name
    else:
        form = res.form
        new_name = '### New Name ###'
        form['name'] = new_name
        res = form.submit()

        # on redirect to detail page
        assert res.url.endswith('/countries/%s' % stub.id)
        res = res.follow()

        # back to detail page
        assert_on_detail_page(res, new_name)
        assert 'Registro alterado com sucesso!' in res
        assert Country.objects.get(pk=stub.pk).name == new_name


@pytest.mark.parametrize("cancel", [True, False])
def test_flux_detail_delete_list(app, cancel):
    stub, res = get_detail_page(app)
    res = res.click('Excluir')

    # on delete page
    assert 'Confirma exclusão de' in res
    assert stub.name in res

    # test bifurcation !
    if cancel:
        res = res.click('Cancelar')

        # back to detail page
        assert_on_detail_page(res, stub.name)
        assert Country.objects.filter(pk=stub.pk)
    else:
        res = res.form.submit()

        # on redirect to list page
        assert res.url.endswith('/countries/')
        res = res.follow()

        # on list page
        assert 'Registro excluído com sucesso!' in res
        assert_h1(res, 'Countries')
        assert not Country.objects.filter(pk=stub.pk)
