import pytest
from django.core.urlresolvers import reverse


@pytest.mark.parametrize("test_input,kwargs,expected", [
    ('sapl.materia:relatoria_update',
        {'pk': '11'},
        '/materia/relatoria/11/edit'),
    ('sapl.materia:tramitacao_update',
        {'pk': '8'},
        '/materia/tramitacao/8/edit'),
    ('sapl.materia:proposicao_create', {}, '/proposicao/create'),
    ('sapl.materia:proposicao_update',
        {'pk': '3'},
        '/proposicao/3/edit'),
    ('sapl.materia:proposicao_list', {}, '/proposicao/'),
])
def test_reverse(test_input, kwargs, expected):
    assert reverse(test_input, kwargs=kwargs) == expected
