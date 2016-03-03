"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from .utils import listify


def test_listify():

    @listify
    def gen():
        yield 1
        yield 2
    assert [1, 2] == gen()
