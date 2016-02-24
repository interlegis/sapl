from pytest import mark

from .utils import listify, make_choices


@mark.parametrize("choice_pairs, result", [
    (
        ['A', 'aaa', 'B', 'bbb'],
        [[('A', 'aaa'), ('B', 'bbb')], 'A', 'B']
    ),
])
def test_make_choices(choice_pairs, result):
    assert list(make_choices(*choice_pairs)) == result


def test_listify():

    @listify
    def gen():
        yield 1
        yield 2
    assert [1, 2] == gen()
