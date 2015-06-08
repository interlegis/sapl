from django.apps import apps
from django.db import models
from inspect import getsourcelines

# adjust FKs base on legacy postgres DDL
pglegapp = apps.get_app_config('pglegacy')
saplapps = {name: apps.get_app_config(name) for name in [
    'parlamentares',
    'comissoes',
    'sessao',
    'materia',
    'norma',
    'lexml',
    'protocoloadm']}

modelname_to_app = {model.__name__: app
                    for appname, app in saplapps.iteritems()
                    for model in app.get_models()}

pgmodels = {model.__name__: model for model in pglegapp.get_models()}


def replace_fks(model, fk_models):

    if model.__name__ not in pgmodels:
        for line in getsourcelines(model)[0]:
            yield line
        return

    pgfields = {f.name: f for f in pgmodels[model.__name__]._meta.fields}
    for line in getsourcelines(model)[0]:
        if line.startswith('class'):
            yield line
        elif ' = models.' in line:
            fieldname = line.split()[0]
            if fieldname not in pgfields:
                if 'cod_' + fieldname in pgfields:
                    fieldname = 'cod_' + fieldname
                else:
                    print '#### Field not in postgres models definition: %s : %s' % (model, fieldname)
                    yield line
                    continue
            pgfield = pgfields[fieldname]

            if isinstance(pgfield, models.ForeignKey):

                # contribute to dependency list
                fk_models.add(pgfield.related_model)

                # remove cod_
                if fieldname.startswith('cod_'):
                    fieldname = fieldname[4:]
                else:
                    print '#### Field does not start with cod_: [%s] !!!' % fieldname

                args = [pgfield.related_model.__name__]
                for karg in ['blank=True', 'null=True']:
                    if karg in line:
                        args += [karg]
                yield '    %s = models.ForeignKey(%s)\n' % (fieldname, ', '.join(args))
            else:
                yield line
        else:
            print '#### Unusual line: [%s] !!!' % line.rstrip('\n')
            yield line


def preplace_fks(app):
    fk_models = set()
    lines = []
    for model in app.get_models():
        for line in replace_fks(model, fk_models):
            lines.append(line)
        lines += ['\n', '\n']

    imports = []
    for model in fk_models:
        if model.__name__ not in modelname_to_app:
            print '#### No app found for %s !!!!!!!' % model.__name__
            continue
        related_app = modelname_to_app[model.__name__]
        if app != related_app:
            imports.append('from %s.models import %s\n' % (
                related_app.name, model.__name__))
    imports = sorted(imports)

    code = '''
from django.db import models

%s
''' % ''.join(imports + ['\n', '\n'] + lines)
    code = code.strip()
    print '######################################################\n\n'
    print code
