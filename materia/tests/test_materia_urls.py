import pytest
from django.core.urlresolvers import reverse


@pytest.mark.parametrize("test_input,kwargs,expected", [
    ('materia:relatoria_update',
        {'pk': '11'},
        '/materia/relatoria/11/edit'),
    ('materia:tramitacao_update',
        {'pk': '8'},
        '/materia/tramitacao/8/edit'),
    ('materia:proposicao_create', {}, '/proposicao/create'),
    ('materia:proposicao_update',
        {'pk': '3'},
        '/proposicao/3/edit'),
    ('materia:proposicao_list', {}, '/proposicao/'),
])
def test_reverse(test_input, kwargs, expected):
    assert reverse(test_input, kwargs=kwargs) == expected
