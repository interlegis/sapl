from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0055_auto_20190816_0943'),
    ]

    operations = [
        migrations.RunSQL("""
            create or replace view materia_materiaemtramitacao as 
            select m.id as id,
                   m.id as materia_id,
                   t.id as tramitacao_id
            from materia_materialegislativa m
            inner join materia_tramitacao t on (m.id = t.materia_id)
            where t.id = (select max(id) from materia_tramitacao where materia_id = m.id)
            order by m.id DESC
        """),
    ]