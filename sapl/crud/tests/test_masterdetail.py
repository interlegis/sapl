import pytest
from django.core.urlresolvers import reverse


@pytest.mark.parametrize('path_name', [
    '/country/1/city         stub_app:city_list',
    '/country/1/city/create  stub_app:city_create',
    '/country/city/1         stub_app:city_detail',
    '/country/city/1/edit    stub_app:city_update',
    '/country/city/1/delete  stub_app:city_delete',
])
def test_reverse(path_name):
    path, name = path_name.split()
    assert path == reverse(name, args=(1,))
