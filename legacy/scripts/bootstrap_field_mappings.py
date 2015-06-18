from collections import defaultdict
from difflib import SequenceMatcher
from os.path import dirname

import yaml

from migration_base import *


# output to bootstrap field_mappings.yaml
for app in appconfs:
    print '\n%s\n%s:' % ('#' * 80, app.name)
    for model in app.models.values():
        print '\n  %s:' % model.__name__
        current_fields = [f.name for f in model._meta.fields]
        legacy_fields = [f.name for f in legacy_app.get_model(model.__name__)._meta.fields if f.name != 'ind_excluido']
        for pair in zip(current_fields, legacy_fields):
            print '    %s : %s' % pair


def similar(a, b): return SequenceMatcher(None, a, b).ratio()

mappings = yaml.load(open(dirname(__file__) + '/field_mappings.yaml', 'r'))

different_pairs = defaultdict(list)
for map in mappings.values():
    for name, fields in map.items():
        for a, b in fields.items():
            if a != 'id' and similar(a, b) < .7:
                different_pairs[name].append((a, b))

if different_pairs:
    print '\n\n######## Different Pairs #########'
    for name, pairs in different_pairs.items():
        print '#', name
        for a, b in pairs:
            print '#  ', a, b
