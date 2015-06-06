from django.apps import apps
from django.db import connection, models

import legacy
from mesa.models import Legislatura, SessaoLegislativa
from parlamentares.models import NivelInstrucao


mappings = (
    (Legislatura, 'num_legislatura', [
        ('dat_inicio', 'data_inicio'),
        ('dat_fim', 'data_fim'),
        ('dat_eleicao', 'data_eleicao'), ]
     ),
    (SessaoLegislativa, 'cod_sessao_leg', [
        ('num_legislatura', 'legislatura'),
        ('num_sessao_leg', 'numero'),
        ('tip_sessao_leg', 'tipo'),
        ('dat_inicio', 'data_inicio'),
        ('dat_fim', 'data_fim'),
        ('dat_inicio_intervalo', 'data_inicio_intervalo'),
        ('dat_fim_intervalo', 'data_fim_intervalo'), ]
     ),
    (NivelInstrucao, 'cod_nivel_instrucao', [
        ('des_nivel_instrucao', 'nivel_instrucao')]
     ),
)


appconfs = [apps.get_app_config(n) for n in [
    'mesa',
    'parlamentares',
    'comissoes',
    'sessao',
    'materia',
    'norma',
    'lexml',
    'protocoloadm', ]]
name_sets = [set(m.__name__ for m in ac.get_models()) for ac in appconfs]

# apps do not overlap
for s1 in name_sets:
    for s2 in name_sets:
        if s1 is not s2:
            assert not s1.intersection(s2)

# apps include all legacy models
legacy_model_names = set(m.__name__ for m in apps.get_app_config('legacy').get_models())
all_names = set()
for s1 in name_sets:
    all_names = all_names.union(s1)
assert all_names == legacy_model_names


def migrate():

    for model, pk, field_pairs in mappings:

        print 'Migrating %s...' % model.__name__

        # clear all model entries
        model.objects.all().delete()
        # resets id sequence
        sql_reset_seq = 'ALTER SEQUENCE %s_id_seq RESTART WITH 1;' % model._meta.db_table
        cursor = connection.cursor()
        cursor.execute(sql_reset_seq)

        legacy_model = getattr(legacy.models, model.__name__)
        for old in legacy_model.objects.all().order_by(pk):
            old_id = getattr(old, pk)
            new = model()
            while not new.id:
                for old_field, new_field in field_pairs:
                    value = getattr(old, old_field)
                    # check for a relation
                    model_field = model._meta.get_field(new_field)
                    if isinstance(model_field, models.ForeignKey):
                        value = model_field.related_model.objects.get(id=value)
                    setattr(new, new_field, value)
                new.save()
                assert new.id <= old_id, 'New id exceeds old one. Be sure your new table was just created!'
                if new.id < old_id:
                    new.delete()
                    new = model()
