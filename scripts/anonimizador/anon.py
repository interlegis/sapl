import random
import re
from collections import defaultdict
from string import digits

from django.apps import apps
from django.db.models.fields import CharField, TextField
from sapl.materia.models import Orgao, Origem
from sapl.norma.models import AssuntoNorma
from sapl.parlamentares.models import Municipio, NivelInstrucao, Partido
from sapl.settings import SAPL_APPS

sapl_appconfs = [apps.get_app_config(n.split('.')[1]) for n in SAPL_APPS]
models = [model for app in sapl_appconfs for model in app.get_models()]

excluidos = Origem, Orgao, AssuntoNorma, Partido, NivelInstrucao, Municipio,

models = [m for m in models
          if 'tipo' not in m._meta.model_name and
          'cargo' not in m._meta.model_name and
          'status' not in m._meta.model_name and
          m not in excluidos and
          m._meta.app_label not in ['compilacao', 'base']]

nomes = [n.strip() for n in open('scripts/anonimizador/nomes.txt').readlines()]

conteudo = open('scripts/anonimizador/paragrafos.txt').read()
pars_list = [p.replace('"', '') for p in re.split('\n\n+', conteudo.strip())]
pars = defaultdict(list)
for p in pars_list:
    pars[round(len(p) / 10)].append(p)
pars = dict(pars)


def change_digits(val):
    return ''.join(random.choice(digits) if a in digits else a for a in val)


def random_text(val):
    if not val or not val.strip():
        return val
    subpars = pars[min(pars.keys(),
                       key=lambda x: abs(x - round(len(val) / 10)))]
    return random.choice(subpars)


def stub(f, obj):
    val = getattr(obj, f.name)
    if isinstance(f, CharField):
        if 'mail' in f.name:
            return 'bla@example.com'
        elif 'nome' in f.name:
            limite = f.max_length or 100000000
            return random.choice(nomes)[:limite]
        elif f.choices:
            return val
        else:
            return change_digits(val)
    if isinstance(f, TextField):
        return random_text(val)
    return val


def anon(model):
    print('--------- %s ---------' % model)
    for obj in model.objects.all():
        for f in model._meta.fields:
            setattr(obj, f.name, stub(f, obj))
        obj.save()


def anon_todos():
    for m in models:
        anon(m)
