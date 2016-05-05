import pytest
from django.core.urlresolvers import reverse


@pytest.mark.parametrize("test_input,kwargs,expected", [
    ('materia:relatoria_update',
        {'pk': '11'},
        '/materia/relatoria/11/edit'),
    ('materia:tramitacao_update',
        {'pk': '8'},
        '/materia/tramitacao/8/edit'),
    ('materia:adicionar_proposicao', {}, '/materia/proposicao'),
    ('materia:editar_proposicao',
        {'pk': '3'},
        '/materia/proposicao/3/edit'),
    ('materia:list_proposicao', {}, '/materia/proposicao_list'),
])
def test_reverse(test_input, kwargs, expected):
    assert reverse(test_input, kwargs=kwargs) == expected
