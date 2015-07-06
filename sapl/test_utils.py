from pytest import mark
from utils import make_choices


@mark.parametrize("choice_pairs, result", [
    (
        ['A', 'aaa', 'B', 'bbb'],
        [[('A', 'aaa'), ('B', 'bbb')], 'A', 'B']
    ),
])
def test_make_choices(choice_pairs, result):
    assert list(make_choices(*choice_pairs)) == result
