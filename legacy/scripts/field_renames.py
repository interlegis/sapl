import re

import yaml
import pkg_resources

from migration_base import appconfs


MODEL_RENAME_PATTERN = re.compile('(.+) \((.+)\)')


field_renames = {}
model_renames = {}
for app in appconfs:
    app_rename_data = yaml.load(pkg_resources.resource_string(app.module.__name__, 'legacy.yaml'))
    for model_name, renames in app_rename_data.items():
        match = MODEL_RENAME_PATTERN.match(model_name)
        if match:
            model_name, old_name = match.groups()
        else:
            old_name = None
        model = getattr(app.models_module, model_name)
        if old_name:
            model_renames[model] = old_name
        field_renames[model] = renames

# collect renames from parent classes
for model, renames in field_renames.items():
    if any(parent in field_renames for parent in model.__mro__[1:]):
        renames = {}
        for parent in reversed(model.__mro__):
            if parent in field_renames:
                renames.update(field_renames[parent])
        field_renames[model] = renames

# remove abstract classes
for model in field_renames:
    if model._meta.abstract:
        del field_renames[model]
