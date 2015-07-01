from collections import defaultdict
from difflib import SequenceMatcher
from inspect import getsourcelines
from collections import OrderedDict

from migration_base import appconfs, legacy_app


def is_unannotated_field_line(line):
    return not line.strip().startswith('#') and ' = ' in line and ' # ' not in line


def is_field_line(line):
    return not line.strip().startswith('#') and ' = ' in line and ' # ' in line


def get_field(line):
    return line.split('=')[0].strip()


def print_commented_source(model):
    new_fields = [f.name for f in model._meta.fields]
    legacy_fields = [f.name for f in legacy_app.get_model(model.__name__)._meta.fields if f.name != 'ind_excluido']
    new_to_old = dict(zip(new_fields, legacy_fields))
    lines = getsourcelines(model)[0]
    cols = max(map(len, [line for line in lines if is_field_line(line)]))
    print '\n'
    for line in lines:
        if not is_unannotated_field_line(line):
            print line.rstrip()
        else:
            print '%s # %s' % (line.rstrip().ljust(cols), new_to_old[get_field(line)])
    return new_to_old


field_renames = OrderedDict()
for app in appconfs:
    for model in app.models.values():
        new_to_old = OrderedDict()
        lines = getsourcelines(model)[0]
        for line in lines:
            if is_field_line(line):
                new = get_field(line)
                old = line.split('#')[-1].strip()
                new_to_old[new] = old
        field_renames[model] = new_to_old


def check_similarity():

    def similar(a, b):
        return SequenceMatcher(None, a, b).ratio()

    different_pairs = defaultdict(list)
    for model, new_to_old in field_renames.items():
        for new, old in new_to_old.items():
            if similar(new, old) < 0.7:
                different_pairs[model].append((new, old))

    if different_pairs:
        print '\n\n######## Different Pairs #########'
        for model, pairs in different_pairs.items():
            print '%s (%s)' % (model.__name__, app.name)
            for a, b in pairs:
                print ' ', a, b
    return different_pairs
