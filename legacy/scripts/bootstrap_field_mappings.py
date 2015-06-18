from inspect import getsourcelines

from collections import defaultdict
from difflib import SequenceMatcher
from os.path import dirname

import yaml

from migration_base import *


def print_field_mappings():
    # output to bootstrap field_mappings.yaml
    for app in appconfs:
        print '\n%s\n%s:' % ('#' * 80, app.name)
        for model in app.models.values():
            print '\n  %s:' % model.__name__
            new_fields = [f.name for f in model._meta.fields]
            legacy_fields = [f.name for f in legacy_app.get_model(
                model.__name__)._meta.fields if f.name != 'ind_excluido']
            for pair in zip(new_fields, legacy_fields):
                print '    %s : %s' % pair

    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

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


def print_commented_source(model):
    new_fields = [f.name for f in model._meta.fields]
    legacy_fields = [f.name for f in legacy_app.get_model(model.__name__)._meta.fields if f.name != 'ind_excluido']
    new_to_old = dict(zip(new_fields, legacy_fields))
    lines = getsourcelines(model)[0]

    def is_field(line):
        return not line.strip().startswith('#') and ' = ' in line

    cols = max(map(len, [line for line in lines if is_field(line)]))
    print '\n'
    for line in lines:
        if not is_field(line):
            print line.rstrip()
        else:
            field = line.split('=')[0].strip()
            print '%s # %s' % (line.rstrip().ljust(cols), new_to_old[field])
