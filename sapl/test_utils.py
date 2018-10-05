from .utils import listify


def test_listify():

    @listify
    def gen():
        yield 1
        yield 2
    assert [1, 2] == gen()
