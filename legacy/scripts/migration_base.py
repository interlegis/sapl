from django.apps import apps


# this order is important for the migration
appconfs = [apps.get_app_config(n) for n in [
    'parlamentares',
    'comissoes',
    'materia',
    'norma',
    'sessao',
    'lexml',
    'protocoloadm', ]]
name_sets = [set(m.__name__ for m in ac.get_models()) for ac in appconfs]

# apps do not overlap
for s1 in name_sets:
    for s2 in name_sets:
        if s1 is not s2:
            assert not s1.intersection(s2)

# apps include all legacy models
legacy_app = apps.get_app_config('legacy')
legacy_model_names = set(m.__name__ for m in legacy_app.get_models())
all_names = set()
for s1 in name_sets:
    all_names = all_names.union(s1)
assert all_names == legacy_model_names


def has_primary_key(model):
    return any(field.primary_key for field in model._meta.fields)

assert all(has_primary_key(model) for model in legacy_app.models.values())
