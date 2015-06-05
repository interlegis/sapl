from django.db import connection

import legacy
from parlamentares.models import NivelInstrucao


mappings = (
    (NivelInstrucao,
        'cod_nivel_instrucao',
     [('des_nivel_instrucao', 'nivel_instrucao')]),
)


def run_legacy_migration():

    for model, pk, field_pairs in mappings:

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
                    setattr(new, new_field, getattr(old, old_field))
                new.save()
                assert new.id <= old_id, 'New id exceeds old one. Be sure your new table was just created!'
                if new.id < old_id:
                    new.delete()
                    new = model()
